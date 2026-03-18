from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MANUFACTURER
from .coordinator import CumminsGeneratorCoordinator


class CumminsGeneratorEntity(CoordinatorEntity[CumminsGeneratorCoordinator]):
    """Common base entity for Cummins generator entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CumminsGeneratorCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(coordinator.domain, coordinator.device_identifier)},
            manufacturer=DEFAULT_MANUFACTURER,
            model=coordinator.device_model,
            name=coordinator.device_name,
        )
