from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant import config_entries, data_entry_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cummins_generator.const import DOMAIN
from custom_components.cummins_generator.modbus_client import (
    ModbusReadError,
    ModbusTimeoutError,
    SerialConnectionError,
)


@pytest.mark.asyncio
async def test_user_flow_success(hass, mock_probe) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "serial_port": "/dev/ttyUSB0",
            "slave": 1,
            "baudrate": 9600,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
            "poll_interval": 10,
            "scan_throttle_ms": 0,
        },
    )

    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert mock_probe.called


@pytest.mark.asyncio
async def test_user_flow_duplicate(hass, mock_probe, entry_data) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Cummins Generator",
        data=entry_data,
        unique_id="/dev/ttyUSB0:1",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)

    assert result["type"] is data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("side_effect", "error_key"),
    [
        (SerialConnectionError("no port"), "cannot_connect"),
        (ModbusTimeoutError("slow"), "timeout"),
        (ModbusReadError("crc"), "modbus_error"),
    ],
)
async def test_user_flow_errors(hass, side_effect, error_key) -> None:
    with patch(
        "custom_components.cummins_generator.config_flow.CumminsModbusClient.probe",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "serial_port": "/dev/ttyUSB0",
                "slave": 1,
                "baudrate": 9600,
                "bytesize": 8,
                "parity": "N",
                "stopbits": 1,
                "poll_interval": 10,
                "scan_throttle_ms": 0,
            },
        )

    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == error_key


@pytest.mark.asyncio
async def test_options_flow_success(hass, mock_probe, entry_data) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Cummins Generator",
        data=entry_data,
        unique_id="/dev/ttyUSB0:1",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            **entry_data,
            "poll_interval": 15,
        },
    )

    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["poll_interval"] == 15
