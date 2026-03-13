from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cummins_gnr8r.const import DOMAIN
from custom_components.cummins_gnr8r.diagnostics import (
    _partially_redact_serial_path,
    async_get_config_entry_diagnostics,
)


def test_partially_redact_serial_path() -> None:
    assert _partially_redact_serial_path("/dev/ttyUSB0") == "/dev/***SB0"
    assert _partially_redact_serial_path("tty0") == "***"


@pytest.mark.asyncio
async def test_async_get_config_entry_diagnostics(hass, entry_data) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="cummins_GNR8R",
        data=entry_data,
        unique_id="/dev/ttyUSB0:1",
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": SimpleNamespace(
            last_update_success=False,
            last_exception_type="ModbusTimeoutError",
            last_exception_message="No response",
            device_identifier="/dev/ttyUSB0:1",
            data=SimpleNamespace(
                group_health={"nfpa_status": True},
                fetched_at=datetime(2026, 3, 13, 12, 0, tzinfo=UTC),
            ),
        )
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["serial_port"] == "/dev/***SB0"
    assert diagnostics["coordinator"]["last_exception_type"] == "ModbusTimeoutError"
    assert diagnostics["coordinator"]["group_health"]["nfpa_status"] is True
