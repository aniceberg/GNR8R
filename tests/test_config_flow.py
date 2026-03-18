from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant import config_entries, data_entry_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cummins_gnr8r.const import (
    BACKEND_ESPHOME_DISCRETE,
    BACKEND_PCC1302_MODBUS,
    CONF_ATS_ON_GENERATOR_ENTITY_ID,
    CONF_BACKEND,
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_GENERATOR_FAULT_ENTITY_ID,
    CONF_GENERATOR_RUNNING_ENTITY_ID,
    CONF_PARITY,
    CONF_POLL_INTERVAL,
    CONF_SCAN_THROTTLE_MS,
    CONF_SERIAL_PORT,
    CONF_SLAVE,
    CONF_STOPBITS,
    CONF_UTILITY_AVAILABLE_ENTITY_ID,
    DOMAIN,
)
from custom_components.cummins_gnr8r.modbus_client import ModbusReadError, ModbusTimeoutError


def _discrete_form_input(discrete_entry_data: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in discrete_entry_data.items()
        if key != CONF_BACKEND and key != CONF_SCAN_THROTTLE_MS
    }


@pytest.mark.asyncio
async def test_discrete_flow_success(hass, discrete_entry_data) -> None:
    for entity_id in (
        discrete_entry_data[CONF_UTILITY_AVAILABLE_ENTITY_ID],
        discrete_entry_data[CONF_ATS_ON_GENERATOR_ENTITY_ID],
        discrete_entry_data[CONF_GENERATOR_RUNNING_ENTITY_ID],
        discrete_entry_data[CONF_GENERATOR_FAULT_ENTITY_ID],
    ):
        hass.states.async_set(entity_id, "off")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_BACKEND: BACKEND_ESPHOME_DISCRETE}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], _discrete_form_input(discrete_entry_data)
    )

    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_BACKEND] == BACKEND_ESPHOME_DISCRETE


@pytest.mark.asyncio
async def test_discrete_flow_missing_entity(hass, discrete_entry_data) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_BACKEND: BACKEND_ESPHOME_DISCRETE}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], _discrete_form_input(discrete_entry_data)
    )

    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == "entity_not_found"


@pytest.mark.asyncio
async def test_modbus_flow_success(hass) -> None:
    with patch(
        "custom_components.cummins_gnr8r.config_flow.validate_modbus_input",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_BACKEND: BACKEND_PCC1302_MODBUS}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_SERIAL_PORT: "/dev/ttyUSB0",
                CONF_SLAVE: 1,
                CONF_BAUDRATE: 9600,
                CONF_BYTESIZE: 8,
                CONF_PARITY: "N",
                CONF_STOPBITS: 1,
                CONF_POLL_INTERVAL: 10,
                CONF_SCAN_THROTTLE_MS: 0,
            },
        )

    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_BACKEND] == BACKEND_PCC1302_MODBUS


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("side_effect", "error_key"),
    [
        (ModbusTimeoutError("slow"), "timeout"),
        (ModbusReadError("crc"), "modbus_error"),
    ],
)
async def test_modbus_flow_errors(hass, side_effect, error_key) -> None:
    with patch(
        "custom_components.cummins_gnr8r.config_flow.validate_modbus_input",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_BACKEND: BACKEND_PCC1302_MODBUS}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_SERIAL_PORT: "/dev/ttyUSB0",
                CONF_SLAVE: 1,
                CONF_BAUDRATE: 9600,
                CONF_BYTESIZE: 8,
                CONF_PARITY: "N",
                CONF_STOPBITS: 1,
                CONF_POLL_INTERVAL: 10,
                CONF_SCAN_THROTTLE_MS: 0,
            },
        )

    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == error_key


@pytest.mark.asyncio
async def test_options_flow_can_switch_backend(hass, config_entry, discrete_entry_data) -> None:
    with patch(
        "custom_components.cummins_gnr8r.config_flow.validate_modbus_input",
        return_value=None,
    ):
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_BACKEND: BACKEND_PCC1302_MODBUS}
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_SERIAL_PORT: "/dev/ttyUSB0",
                CONF_SLAVE: 1,
                CONF_BAUDRATE: 19200,
                CONF_BYTESIZE: 8,
                CONF_PARITY: "N",
                CONF_STOPBITS: 1,
                CONF_POLL_INTERVAL: 15,
                CONF_SCAN_THROTTLE_MS: 100,
            },
        )

    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_BACKEND] == BACKEND_PCC1302_MODBUS


@pytest.mark.asyncio
async def test_duplicate_modbus_flow_aborts(hass) -> None:
    existing = MockConfigEntry(
        domain=DOMAIN,
        title="cummins_GNR8R",
        data={
            CONF_BACKEND: BACKEND_PCC1302_MODBUS,
            CONF_SERIAL_PORT: "/dev/ttyUSB0",
            CONF_SLAVE: 1,
            CONF_BAUDRATE: 9600,
            CONF_BYTESIZE: 8,
            CONF_PARITY: "N",
            CONF_STOPBITS: 1,
            CONF_POLL_INTERVAL: 10,
            CONF_SCAN_THROTTLE_MS: 0,
        },
    )
    existing.add_to_hass(hass)

    with patch(
        "custom_components.cummins_gnr8r.config_flow.validate_modbus_input",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_BACKEND: BACKEND_PCC1302_MODBUS}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_SERIAL_PORT: "/dev/ttyUSB0",
                CONF_SLAVE: 1,
                CONF_BAUDRATE: 9600,
                CONF_BYTESIZE: 8,
                CONF_PARITY: "N",
                CONF_STOPBITS: 1,
                CONF_POLL_INTERVAL: 10,
                CONF_SCAN_THROTTLE_MS: 0,
            },
        )

    assert result["type"] is data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"
