from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .modbus_client import (
    CumminsGeneratorError,
    CumminsModbusClient,
)
from .models import CoordinatorSnapshot, RegisterGroup
from .register_map import (
    ALL_DEFINED_REGISTERS,
    BINARY_SENSOR_TYPES,
    BITMAP_SENSOR_TYPES,
    REGISTER_GROUPS,
    SENSOR_TYPES,
    bit_is_set,
    scale_register_value,
)

_LOGGER = logging.getLogger(__name__)


class CumminsGeneratorCoordinator(DataUpdateCoordinator[CoordinatorSnapshot]):
    """Coordinate Modbus polling for a single generator."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: CumminsModbusClient,
        poll_interval_seconds: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval_seconds),
        )
        self.client = client
        self.domain = DOMAIN
        self.device_identifier = f"{client.params.port}:{client.params.slave}"
        self.device_name = "cummins_GNR8R"
        self.last_exception_type: str | None = None
        self.last_exception_message: str | None = None

    async def _async_update_data(self) -> CoordinatorSnapshot:
        """Poll all required register groups."""
        values: dict[str, int | float | bool | None] = {}
        register_availability = dict.fromkeys(ALL_DEFINED_REGISTERS, False)
        group_health: dict[str, bool] = {}

        try:
            register_values = await self._async_read_groups(REGISTER_GROUPS)
        except CumminsGeneratorError as err:
            self.last_exception_type = type(err).__name__
            self.last_exception_message = str(err)
            raise UpdateFailed(str(err)) from err

        self.last_exception_type = None
        self.last_exception_message = None

        for group_key, group_result in register_values.items():
            group_health[group_key] = group_result is not None
            if group_result is None:
                continue
            for register, raw_value in group_result.items():
                register_availability[register] = True
                values[f"register_{register}"] = raw_value

        for description in SENSOR_TYPES:
            raw_value = register_values_for(register_values, description.register)
            values[description.key] = (
                scale_register_value(raw_value, description.scale)
                if raw_value is not None
                else None
            )

        for description in BITMAP_SENSOR_TYPES:
            values[description.key] = register_values_for(register_values, description.register)

        for description in BINARY_SENSOR_TYPES:
            register_value = register_values_for(register_values, description.register)
            values[description.key] = (
                bit_is_set(register_value, description.bit) if register_value is not None else None
            )

        return CoordinatorSnapshot(
            values=values,
            register_availability=register_availability,
            group_health=group_health,
            fetched_at=dt_util.utcnow(),
        )

    async def _async_read_groups(
        self, groups: tuple[RegisterGroup, ...]
    ) -> dict[str, dict[int, int] | None]:
        """Read configured register groups through the executor."""
        results: dict[str, dict[int, int] | None] = {}

        for group in groups:
            try:
                registers = await self.hass.async_add_executor_job(
                    self.client.read_holding_registers,
                    group.start_address,
                    group.count,
                )
            except CumminsGeneratorError as err:
                if group.key == "nfpa_status":
                    raise
                _LOGGER.debug("Register group %s unavailable: %s", group.key, err)
                results[group.key] = None
                continue

            results[group.key] = {
                group.start_address + offset: value for offset, value in enumerate(registers)
            }

        return results


def register_values_for(
    register_groups: Mapping[str, dict[int, int] | None], register: int
) -> int | None:
    """Return a register value from grouped results."""
    for group_result in register_groups.values():
        if group_result and register in group_result:
            return group_result[register]
    return None
