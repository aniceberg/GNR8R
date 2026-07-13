from __future__ import annotations

from unittest.mock import Mock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cummins_gnr8r.backends.pcc1302_modbus import (
    PCC1302ModbusBackend,
    _decode_values,
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


def test_decode_values_expands_nfpa_and_extended_bitmaps() -> None:
    nfpa_bits = (15, 14, 13, 12, 10, 9, 8, 5, 3, 2, 0)
    extended_bits = (15, 14, 13, 12, 11, 9, 7, 6, 5, 4, 3, 2, 1, 0)
    nfpa_bitmap = sum(1 << bit for bit in nfpa_bits)
    extended_bitmap = sum(1 << bit for bit in extended_bits)

    values = _decode_values(
        {
            "status": {40716: nfpa_bitmap, 40717: extended_bitmap},
            "metrics_a": {40735: 127, 40736: 205, 40737: 0, 40738: 2955},
            "metrics_b": {40742: 1800, 40743: 14, 40744: 0, 40745: 25},
            "frequency": {40750: 600},
        }
    )

    for key in (
        "not_in_auto",
        "low_battery_voltage_alarm",
        "charger_ac_failure",
        "fail_to_start",
        "high_engine_temperature",
        "low_oil_pressure_alarm",
        "overspeed",
        "low_fuel_level",
        "test_exercise_in_progress",
        "load_shed",
        "transfer_inhibit_active",
        "retransfer_inhibit_active",
        "fail_to_close",
        "fail_to_disconnect",
        "fail_to_synchronize",
        "bypass_to_source_1",
        "bypass_to_source_2",
    ):
        assert values[key] is True
    assert values["action_required"] is True


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
        [123, 1],
        [80, 150],
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
    assert update.values["current_fault_code"] == 123
    assert update.values["current_fault_type"] == "warning"
    assert update.values["genset_load_percent"] == 40.0
    assert update.values["genset_total_kw"] == 150.0
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
        ModbusReadError("unsupported"),
        ModbusReadError("unsupported"),
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
