from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_PARITY,
    CONF_POLL_INTERVAL,
    CONF_SCAN_THROTTLE_MS,
    CONF_SERIAL_PORT,
    CONF_SLAVE,
    CONF_STOPBITS,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_PARITY,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_SCAN_THROTTLE_MS,
    DEFAULT_SLAVE,
    DEFAULT_STOPBITS,
    DOMAIN,
    REGISTER_BATTERY_VOLTAGE,
    REGISTER_ENGINE_SPEED,
)
from .modbus_client import (
    CumminsGeneratorError,
    CumminsModbusClient,
    ModbusReadError,
    ModbusTimeoutError,
    SerialConnectionError,
    SerialConnectionParams,
)


def _base_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    data = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_SERIAL_PORT, default=data.get(CONF_SERIAL_PORT, "/dev/ttyUSB0")): str,
            vol.Required(CONF_SLAVE, default=data.get(CONF_SLAVE, DEFAULT_SLAVE)): vol.All(
                int, vol.Range(min=1, max=247)
            ),
            vol.Required(CONF_BAUDRATE, default=data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)): vol.In(
                [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
            ),
            vol.Required(CONF_BYTESIZE, default=data.get(CONF_BYTESIZE, DEFAULT_BYTESIZE)): vol.In(
                [7, 8]
            ),
            vol.Required(CONF_PARITY, default=data.get(CONF_PARITY, DEFAULT_PARITY)): vol.In(
                ["N", "E", "O"]
            ),
            vol.Required(CONF_STOPBITS, default=data.get(CONF_STOPBITS, DEFAULT_STOPBITS)): vol.In(
                [1, 2]
            ),
            vol.Required(
                CONF_POLL_INTERVAL,
                default=data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
            ): vol.All(int, vol.Range(min=5, max=300)),
            vol.Required(
                CONF_SCAN_THROTTLE_MS,
                default=data.get(CONF_SCAN_THROTTLE_MS, DEFAULT_SCAN_THROTTLE_MS),
            ): vol.All(int, vol.Range(min=0, max=5000)),
        }
    )


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate a config flow entry by probing safe registers."""
    client = CumminsModbusClient(
        SerialConnectionParams(
            port=data[CONF_SERIAL_PORT],
            slave=data[CONF_SLAVE],
            baudrate=data[CONF_BAUDRATE],
            bytesize=data[CONF_BYTESIZE],
            parity=data[CONF_PARITY],
            stopbits=data[CONF_STOPBITS],
            poll_interval=data[CONF_POLL_INTERVAL],
            scan_throttle_ms=data[CONF_SCAN_THROTTLE_MS],
        )
    )
    await hass.async_add_executor_job(
        client.probe, (REGISTER_BATTERY_VOLTAGE, REGISTER_ENGINE_SPEED)
    )


class CumminsGeneratorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for cummins_GNR8R."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_SERIAL_PORT]}:{user_input[CONF_SLAVE]}"
            )
            self._abort_if_unique_id_configured()
            try:
                await validate_input(self.hass, user_input)
            except SerialConnectionError:
                errors["base"] = "cannot_connect"
            except ModbusTimeoutError:
                errors["base"] = "timeout"
            except ModbusReadError:
                errors["base"] = "modbus_error"
            except CumminsGeneratorError:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="cummins_GNR8R", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_base_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return CumminsGeneratorOptionsFlow(config_entry)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return await CumminsGeneratorOptionsFlow(self._get_reconfigure_entry()).async_step_init(
            user_input
        )


class CumminsGeneratorOptionsFlow(config_entries.OptionsFlowWithConfigEntry):
    """Options flow for cummins_GNR8R."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        current = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except SerialConnectionError:
                errors["base"] = "cannot_connect"
            except ModbusTimeoutError:
                errors["base"] = "timeout"
            except ModbusReadError:
                errors["base"] = "modbus_error"
            except CumminsGeneratorError:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_base_schema(current),
            errors=errors,
        )
