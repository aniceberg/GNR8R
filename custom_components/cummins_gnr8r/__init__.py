from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_PARITY,
    CONF_POLL_INTERVAL,
    CONF_SCAN_THROTTLE_MS,
    CONF_SERIAL_PORT,
    CONF_SLAVE,
    CONF_STOPBITS,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import CumminsGeneratorCoordinator
from .modbus_client import CumminsModbusClient, SerialConnectionParams

type CumminsConfigEntry = ConfigEntry[dict[str, Any]]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration via config entries only."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: CumminsConfigEntry) -> bool:
    """Set up a Cummins generator config entry."""
    params = _params_from_entry(entry)
    client = CumminsModbusClient(params)
    coordinator = CumminsGeneratorCoordinator(
        hass=hass,
        client=client,
        poll_interval_seconds=params.poll_interval,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_COORDINATOR: coordinator,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CumminsConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: CumminsConfigEntry) -> None:
    """Reload a config entry after options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _params_from_entry(entry: CumminsConfigEntry) -> SerialConnectionParams:
    data = {**entry.data, **entry.options}
    return SerialConnectionParams(
        port=data[CONF_SERIAL_PORT],
        slave=data[CONF_SLAVE],
        baudrate=data[CONF_BAUDRATE],
        bytesize=data[CONF_BYTESIZE],
        parity=data[CONF_PARITY],
        stopbits=data[CONF_STOPBITS],
        poll_interval=data[CONF_POLL_INTERVAL],
        scan_throttle_ms=data[CONF_SCAN_THROTTLE_MS],
    )
