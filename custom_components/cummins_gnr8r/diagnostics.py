from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_PARITY,
    CONF_POLL_INTERVAL,
    CONF_SCAN_THROTTLE_MS,
    CONF_SERIAL_PORT,
    CONF_SLAVE,
    CONF_STOPBITS,
    DATA_COORDINATOR,
    DOMAIN,
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> Mapping[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    data = {**entry.data, **entry.options}
    diagnostics = {
        "entry": {
            CONF_SERIAL_PORT: _partially_redact_serial_path(data[CONF_SERIAL_PORT]),
            CONF_SLAVE: data[CONF_SLAVE],
            CONF_BAUDRATE: data[CONF_BAUDRATE],
            CONF_BYTESIZE: data[CONF_BYTESIZE],
            CONF_PARITY: data[CONF_PARITY],
            CONF_STOPBITS: data[CONF_STOPBITS],
            CONF_POLL_INTERVAL: data[CONF_POLL_INTERVAL],
            CONF_SCAN_THROTTLE_MS: data[CONF_SCAN_THROTTLE_MS],
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_exception_type": coordinator.last_exception_type,
            "last_exception_message": coordinator.last_exception_message,
            "device_identifier": coordinator.device_identifier,
            "group_health": coordinator.data.group_health if coordinator.data else {},
            "fetched_at": coordinator.data.fetched_at.isoformat() if coordinator.data else None,
        },
    }
    return diagnostics


def _partially_redact_serial_path(value: str) -> str:
    """Partially redact a serial path while keeping it recognizable."""
    if len(value) <= 5:
        return "***"
    return f"{value[:5]}***{value[-3:]}"
