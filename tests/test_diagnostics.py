from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cummins_gnr8r.const import (
    BACKEND_ESPHOME_DISCRETE,
    BACKEND_PCC1302_MODBUS,
    CONF_BACKEND,
    CONF_POLL_INTERVAL,
    CONF_SCAN_THROTTLE_MS,
    CONF_UTILITY_AVAILABLE_ENTITY_ID,
    DOMAIN,
)
from custom_components.cummins_gnr8r.diagnostics import (
    _partially_redact_serial_path,
    async_get_config_entry_diagnostics,
)


def test_partially_redact_serial_path() -> None:
    assert _partially_redact_serial_path("/dev/ttyUSB0") == "/dev/***SB0"


@pytest.mark.asyncio
async def test_discrete_diagnostics(hass, discrete_entry_data) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="cummins_GNR8R",
        data=discrete_entry_data,
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": SimpleNamespace(
            last_update_success=True,
            last_exception_type=None,
            last_exception_message=None,
            device_identifier="test",
            data=SimpleNamespace(
                backend=BACKEND_ESPHOME_DISCRETE,
                details={"source_states": {}},
                fetched_at=datetime(2026, 3, 17, 12, 0, tzinfo=UTC),
            ),
        )
    }
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["entry"][CONF_BACKEND] == BACKEND_ESPHOME_DISCRETE
    assert (
        diagnostics["entry"][CONF_UTILITY_AVAILABLE_ENTITY_ID] == "binary_sensor.utility_available"
    )
    assert diagnostics["coordinator"]["backend"] == BACKEND_ESPHOME_DISCRETE


@pytest.mark.asyncio
async def test_modbus_diagnostics_redacts_serial_path(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="cummins_GNR8R",
        data={
            CONF_BACKEND: BACKEND_PCC1302_MODBUS,
            "serial_port": "/dev/ttyUSB0",
            "slave": 1,
            "baudrate": 9600,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
            CONF_POLL_INTERVAL: 10,
            CONF_SCAN_THROTTLE_MS: 0,
        },
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": SimpleNamespace(
            last_update_success=False,
            last_exception_type="ModbusTimeoutError",
            last_exception_message="No response",
            device_identifier="test",
            data=SimpleNamespace(
                backend=BACKEND_PCC1302_MODBUS,
                details={"group_health": {"status": True}},
                fetched_at=datetime(2026, 3, 17, 12, 0, tzinfo=UTC),
            ),
        )
    }
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["entry"]["serial_port"] == "/dev/***SB0"
    assert diagnostics["coordinator"]["backend"] == BACKEND_PCC1302_MODBUS
