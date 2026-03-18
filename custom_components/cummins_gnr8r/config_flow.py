from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .backends.base import DiscreteEntityValidationError
from .backends.esphome_discrete import async_validate_entity_mappings, build_discrete_mappings
from .backends.pcc1302_modbus import async_validate_modbus_backend
from .const import (
    BACKEND_ESPHOME_DISCRETE,
    BACKEND_PCC1302_MODBUS,
    BACKENDS,
    CONF_ATS_ON_GENERATOR_ENTITY_ID,
    CONF_BACKEND,
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_GENERATOR_FAULT_ENTITY_ID,
    CONF_GENERATOR_RUNNING_ENTITY_ID,
    CONF_INVERT_ATS_ON_GENERATOR,
    CONF_INVERT_GENERATOR_FAULT,
    CONF_INVERT_GENERATOR_RUNNING,
    CONF_INVERT_UTILITY_AVAILABLE,
    CONF_PARITY,
    CONF_POLL_INTERVAL,
    CONF_SCAN_THROTTLE_MS,
    CONF_SERIAL_PORT,
    CONF_SLAVE,
    CONF_STOPBITS,
    CONF_UTILITY_AVAILABLE_ENTITY_ID,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_PARITY,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_SCAN_THROTTLE_MS,
    DEFAULT_SLAVE,
    DEFAULT_STOPBITS,
    DOMAIN,
)
from .modbus_client import (
    CumminsGeneratorError,
    CumminsModbusClient,
    ModbusReadError,
    ModbusTimeoutError,
    SerialConnectionError,
    SerialConnectionParams,
)


def _backend_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    data = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_BACKEND,
                default=data.get(CONF_BACKEND, BACKEND_ESPHOME_DISCRETE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=list(BACKENDS),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="backend",
                )
            )
        }
    )


def _discrete_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    data = defaults or {}
    entity_selector = selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor"))
    return vol.Schema(
        {
            vol.Required(
                CONF_UTILITY_AVAILABLE_ENTITY_ID,
                default=data.get(CONF_UTILITY_AVAILABLE_ENTITY_ID, ""),
            ): entity_selector,
            vol.Required(
                CONF_ATS_ON_GENERATOR_ENTITY_ID,
                default=data.get(CONF_ATS_ON_GENERATOR_ENTITY_ID, ""),
            ): entity_selector,
            vol.Required(
                CONF_GENERATOR_RUNNING_ENTITY_ID,
                default=data.get(CONF_GENERATOR_RUNNING_ENTITY_ID, ""),
            ): entity_selector,
            vol.Required(
                CONF_GENERATOR_FAULT_ENTITY_ID,
                default=data.get(CONF_GENERATOR_FAULT_ENTITY_ID, ""),
            ): entity_selector,
            vol.Required(
                CONF_INVERT_UTILITY_AVAILABLE,
                default=data.get(CONF_INVERT_UTILITY_AVAILABLE, False),
            ): bool,
            vol.Required(
                CONF_INVERT_ATS_ON_GENERATOR,
                default=data.get(CONF_INVERT_ATS_ON_GENERATOR, False),
            ): bool,
            vol.Required(
                CONF_INVERT_GENERATOR_RUNNING,
                default=data.get(CONF_INVERT_GENERATOR_RUNNING, False),
            ): bool,
            vol.Required(
                CONF_INVERT_GENERATOR_FAULT,
                default=data.get(CONF_INVERT_GENERATOR_FAULT, False),
            ): bool,
            vol.Required(
                CONF_POLL_INTERVAL,
                default=data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
            ): vol.All(int, vol.Range(min=5, max=300)),
        }
    )


def _modbus_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
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


async def validate_discrete_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate mapped binary-sensor entity IDs."""
    await async_validate_entity_mappings(hass, build_discrete_mappings(data))


async def validate_modbus_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the Modbus backend."""
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
    await async_validate_modbus_backend(hass, client)


class CumminsGeneratorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for cummins_GNR8R."""

    VERSION = 1

    def __init__(self) -> None:
        self._config_data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Choose the backend."""
        if user_input is not None:
            self._config_data = dict(user_input)
            if user_input[CONF_BACKEND] == BACKEND_ESPHOME_DISCRETE:
                return await self.async_step_esphome_discrete()
            return await self.async_step_pcc1302_modbus()

        return self.async_show_form(
            step_id="user",
            data_schema=_backend_schema(self._config_data),
            errors={},
        )

    async def async_step_esphome_discrete(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure the discrete backend."""
        errors: dict[str, str] = {}
        defaults = {**self._config_data, **(user_input or {})}
        if user_input is not None:
            final_data = {
                **self._config_data,
                **user_input,
                CONF_BACKEND: BACKEND_ESPHOME_DISCRETE,
                CONF_SCAN_THROTTLE_MS: 0,
            }
            try:
                await validate_discrete_input(self.hass, final_data)
            except DiscreteEntityValidationError:
                errors["base"] = "entity_not_found"
            else:
                if _is_duplicate(self.hass, final_data):
                    return self.async_abort(reason="already_configured")
                return self.async_create_entry(title="cummins_GNR8R", data=final_data)

        return self.async_show_form(
            step_id=BACKEND_ESPHOME_DISCRETE,
            data_schema=_discrete_schema(defaults),
            errors=errors,
        )

    async def async_step_pcc1302_modbus(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure the Modbus backend."""
        errors: dict[str, str] = {}
        defaults = {**self._config_data, **(user_input or {})}
        if user_input is not None:
            final_data = {
                **self._config_data,
                **user_input,
                CONF_BACKEND: BACKEND_PCC1302_MODBUS,
            }
            try:
                await validate_modbus_input(self.hass, final_data)
            except SerialConnectionError:
                errors["base"] = "cannot_connect"
            except ModbusTimeoutError:
                errors["base"] = "timeout"
            except ModbusReadError:
                errors["base"] = "modbus_error"
            except CumminsGeneratorError:
                errors["base"] = "unknown"
            else:
                if _is_duplicate(self.hass, final_data):
                    return self.async_abort(reason="already_configured")
                return self.async_create_entry(title="cummins_GNR8R", data=final_data)

        return self.async_show_form(
            step_id=BACKEND_PCC1302_MODBUS,
            data_schema=_modbus_schema(defaults),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return CumminsGeneratorOptionsFlow(config_entry)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Support reconfiguration from the config entry screen."""
        return await CumminsGeneratorOptionsFlow(self._get_reconfigure_entry()).async_step_init(
            user_input
        )


class CumminsGeneratorOptionsFlow(config_entries.OptionsFlowWithConfigEntry):
    """Options and reconfigure flow for cummins_GNR8R."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Choose a backend during options/reconfigure."""
        current = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            if user_input[CONF_BACKEND] == BACKEND_ESPHOME_DISCRETE:
                return await self.async_step_esphome_discrete()
            return await self.async_step_pcc1302_modbus()

        return self.async_show_form(
            step_id="init",
            data_schema=_backend_schema(current),
            errors={},
        )

    async def async_step_esphome_discrete(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Update discrete backend settings."""
        current = {
            **self.config_entry.data,
            **self.config_entry.options,
            CONF_BACKEND: BACKEND_ESPHOME_DISCRETE,
        }
        errors: dict[str, str] = {}
        if user_input is not None:
            updated = {
                **current,
                **user_input,
                CONF_BACKEND: BACKEND_ESPHOME_DISCRETE,
                CONF_SCAN_THROTTLE_MS: 0,
            }
            try:
                await validate_discrete_input(self.hass, updated)
            except DiscreteEntityValidationError:
                errors["base"] = "entity_not_found"
            else:
                if _is_duplicate(self.hass, updated, self.config_entry):
                    return self.async_abort(reason="already_configured")
                return self.async_create_entry(title="", data=updated)

        return self.async_show_form(
            step_id=BACKEND_ESPHOME_DISCRETE,
            data_schema=_discrete_schema(current),
            errors=errors,
        )

    async def async_step_pcc1302_modbus(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Update PCC1302 Modbus settings."""
        current = {
            **self.config_entry.data,
            **self.config_entry.options,
            CONF_BACKEND: BACKEND_PCC1302_MODBUS,
        }
        errors: dict[str, str] = {}
        if user_input is not None:
            updated = {**current, **user_input, CONF_BACKEND: BACKEND_PCC1302_MODBUS}
            try:
                await validate_modbus_input(self.hass, updated)
            except SerialConnectionError:
                errors["base"] = "cannot_connect"
            except ModbusTimeoutError:
                errors["base"] = "timeout"
            except ModbusReadError:
                errors["base"] = "modbus_error"
            except CumminsGeneratorError:
                errors["base"] = "unknown"
            else:
                if _is_duplicate(self.hass, updated, self.config_entry):
                    return self.async_abort(reason="already_configured")
                return self.async_create_entry(title="", data=updated)

        return self.async_show_form(
            step_id=BACKEND_PCC1302_MODBUS,
            data_schema=_modbus_schema(current),
            errors=errors,
        )


def _entry_identity(data: dict[str, Any]) -> str:
    """Create a duplicate-detection identity for a config entry."""
    if data[CONF_BACKEND] == BACKEND_PCC1302_MODBUS:
        return f"modbus:{data[CONF_SERIAL_PORT]}:{data[CONF_SLAVE]}"
    return "discrete:" + ",".join(
        sorted(
            (
                data[CONF_UTILITY_AVAILABLE_ENTITY_ID],
                data[CONF_ATS_ON_GENERATOR_ENTITY_ID],
                data[CONF_GENERATOR_RUNNING_ENTITY_ID],
                data[CONF_GENERATOR_FAULT_ENTITY_ID],
            )
        )
    )


def _is_duplicate(
    hass: HomeAssistant,
    candidate: dict[str, Any],
    current_entry: config_entries.ConfigEntry | None = None,
) -> bool:
    """Return True when another entry already matches the backend identity."""
    candidate_identity = _entry_identity(candidate)
    for entry in hass.config_entries.async_entries(DOMAIN):
        if current_entry is not None and entry.entry_id == current_entry.entry_id:
            continue
        current = {**entry.data, **entry.options}
        if _entry_identity(current) == candidate_identity:
            return True
    return False
