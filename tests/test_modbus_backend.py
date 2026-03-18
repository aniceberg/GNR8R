from __future__ import annotations

from unittest.mock import Mock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cummins_gnr8r.backends.pcc1302_modbus import (
    PCC1302ModbusBackend,
    bit_is_set,
    decode_u32,
)
from custom_components.cummins_gnr8r.coordinator import CumminsGeneratorCoordinator
from custom_components.cummins_gnr8r.modbus_client import ModbusReadError, SerialConnectionParams


def test_decode_u32() -> None:
    assert decode_u32(0x0001, 0x0002) == 65538


def test_bit_is_set() -> None:
    assert bit_is_set(0b1000_0000_0000_0001, 15) is True
    assert bit_is_set(0b1000_0000_0000_0001, 0) is True
    assert bit_is_set(0b1000_0000_0000_0001, 7) is False


@pytest.mark.asyncio
async def test_modbus_backend_decodes_registers(hass) -> None:
    client = Mock()
    client.params = SerialConnectionParams(
        port="/dev/ttyUSB0",
        slave=1,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        poll_interval=10,
    )
    client.read_holding_registers.side_effect = [
        [0xA000, 0x8001],
        [127, 205, 0, 2955],
        [1800, 14, 0, 25],
        [600],
        ModbusReadError("unsupported"),
        ModbusReadError("unsupported"),
        ModbusReadError("unsupported"),
    ]

    backend = PCC1302ModbusBackend(hass, client)
    update = await backend.async_fetch()

    assert update.values["battery_voltage"] == 12.7
    assert update.values["oil_pressure"] == 20.5
    assert update.values["coolant_temperature_c"] == 22.4
    assert update.values["coolant_temperature_f"] == 72.3
    assert update.values["engine_speed"] == 1800
    assert update.values["engine_runtime"] == 25
    assert update.values["modbus_common_alarm"] is True
    assert update.logical_signals["generator_running"] is True
    assert update.logical_signals["generator_fault"] is True
    assert update.logical_signals["utility_available"] is None
    assert update.logical_signals["ats_on_generator"] is None


@pytest.mark.asyncio
async def test_modbus_backend_decodes_optional_ats_and_utility_registers(hass) -> None:
    client = Mock()
    client.params = SerialConnectionParams(
        port="/dev/ttyUSB0",
        slave=1,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        poll_interval=10,
    )
    client.read_holding_registers.side_effect = [
        [0x2000, 0x0000],
        [127, 205, 0, 2955],
        [1800, 14, 0, 25],
        [600],
        [9, 1, 2, 0, 0, 0, 0, 0x8000, 0xF800],
        [120],
        [600],
    ]

    backend = PCC1302ModbusBackend(hass, client)
    update = await backend.async_fetch()

    assert update.values["ats_mode"] == "utility_genset"
    assert update.values["ats_state"] == "source_2_connected"
    assert update.values["source_1_available"] is True
    assert update.values["source_2_connected"] is True
    assert update.values["ats_common_alarm"] is True
    assert update.values["utility_ln_average_voltage"] == 120.0
    assert update.values["utility_frequency"] == 60.0
    assert update.logical_signals["utility_available"] is True
    assert update.logical_signals["ats_on_generator"] is True


@pytest.mark.asyncio
async def test_modbus_backend_skips_ats_derivation_when_mode_is_not_utility_genset(hass) -> None:
    client = Mock()
    client.params = SerialConnectionParams(
        port="/dev/ttyUSB0",
        slave=1,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        poll_interval=10,
    )
    client.read_holding_registers.side_effect = [
        [0x2000, 0x0000],
        [127, 205, 0, 2955],
        [1800, 14, 0, 25],
        [600],
        [9, 2, 1, 0, 0, 0, 0, 0x8000, 0xE000],
        ModbusReadError("unsupported"),
        ModbusReadError("unsupported"),
    ]

    backend = PCC1302ModbusBackend(hass, client)
    update = await backend.async_fetch()

    assert update.values["ats_mode"] == "utility_utility"
    assert update.logical_signals["utility_available"] is None
    assert update.logical_signals["ats_on_generator"] is None


@pytest.mark.asyncio
async def test_coordinator_marks_unavailable_on_modbus_failure(hass) -> None:
    client = Mock()
    client.params = SerialConnectionParams(
        port="/dev/ttyUSB0",
        slave=1,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        poll_interval=10,
    )
    client.read_holding_registers.side_effect = [ModbusReadError("crc error")]
    backend = PCC1302ModbusBackend(hass, client)
    entry = MockConfigEntry(domain="cummins_gnr8r", title="cummins_GNR8R", data={})

    coordinator = CumminsGeneratorCoordinator(hass, entry, backend, 10)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
