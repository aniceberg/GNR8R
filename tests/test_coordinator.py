from __future__ import annotations

from unittest.mock import Mock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.cummins_gnr8r.coordinator import CumminsGeneratorCoordinator
from custom_components.cummins_gnr8r.modbus_client import (
    ModbusReadError,
    SerialConnectionParams,
)


@pytest.mark.asyncio
async def test_coordinator_success(hass) -> None:
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
        [0xA001, 0x8001],
        [600],
        [127, 205, 0, 870, 0, 0, 0, 1800, 14],
    ]

    coordinator = CumminsGeneratorCoordinator(hass, client, 10)
    snapshot = await coordinator._async_update_data()

    assert snapshot.values["battery_voltage"] == 12.7
    assert snapshot.values["engine_speed"] == 1800
    assert snapshot.values["common_alarm"] is True
    assert snapshot.values["emergency_stop"] is True
    assert snapshot.group_health["engine_metrics"] is True


@pytest.mark.asyncio
async def test_coordinator_partial_group_failure(hass) -> None:
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
        [0, 0],
        [600],
        ModbusReadError("group unavailable"),
    ]

    coordinator = CumminsGeneratorCoordinator(hass, client, 10)
    snapshot = await coordinator._async_update_data()

    assert snapshot.group_health["engine_metrics"] is False
    assert snapshot.values["battery_voltage"] is None
    assert snapshot.values["average_line_frequency"] == 60.0


@pytest.mark.asyncio
async def test_coordinator_raises_for_nfpa_failure(hass) -> None:
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
    client.read_holding_registers.side_effect = [ModbusReadError("bad CRC")]

    coordinator = CumminsGeneratorCoordinator(hass, client, 10)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    assert coordinator.last_exception_type == "ModbusReadError"
