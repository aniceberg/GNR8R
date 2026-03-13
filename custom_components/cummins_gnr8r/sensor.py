from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .entity import CumminsGeneratorEntity
from .models import BitmapSensorDescription, SensorDescription
from .register_map import BITMAP_SENSOR_TYPES, SENSOR_TYPES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = [
        CumminsRegisterSensor(coordinator, entry, description) for description in SENSOR_TYPES
    ] + [
        CumminsBitmapSensor(coordinator, entry, description) for description in BITMAP_SENSOR_TYPES
    ]
    async_add_entities(entities)


class CumminsRegisterSensor(CumminsGeneratorEntity, SensorEntity):
    """Scalar register-backed sensor."""

    entity_description: SensorDescription

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: SensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_translation_key = description.key
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_entity_category = description.entity_category
        self._attr_suggested_display_precision = description.suggested_display_precision

    @property
    def native_value(self):
        return self.coordinator.data.values.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        return super().available and self.native_value is not None


class CumminsBitmapSensor(CumminsGeneratorEntity, SensorEntity):
    """Raw NFPA bitmap sensor."""

    entity_description: BitmapSensorDescription

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: BitmapSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_translation_key = description.key
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_entity_category = description.entity_category
        self._attr_icon = "mdi:form-select"

    @property
    def native_value(self):
        return self.coordinator.data.values.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        return super().available and self.native_value is not None
