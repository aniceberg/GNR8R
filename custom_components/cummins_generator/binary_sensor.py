from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .entity import CumminsGeneratorEntity
from .models import BinarySensorDescription
from .register_map import BINARY_SENSOR_TYPES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        CumminsBinarySensor(coordinator, entry, description) for description in BINARY_SENSOR_TYPES
    )


class CumminsBinarySensor(CumminsGeneratorEntity, BinarySensorEntity):
    """Bitmap-derived binary sensor."""

    entity_description: BinarySensorDescription

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: BinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_translation_key = description.key
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_class = description.device_class
        self._attr_entity_category = description.entity_category

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.values.get(self.entity_description.key)
        return value if isinstance(value, bool) else None

    @property
    def available(self) -> bool:
        return super().available and self.is_on is not None
