from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    DATA_COORDINATOR,
    DERIVED_RUNNING_ON_GENERATOR,
    DERIVED_TRANSFER_IN_PROGRESS,
    DERIVED_UTILITY_OUTAGE_ACTIVE,
    DOMAIN,
    ROLE_ATS_ON_GENERATOR,
    ROLE_GENERATOR_FAULT,
    ROLE_GENERATOR_RUNNING,
    ROLE_UTILITY_AVAILABLE,
)
from .entity import CumminsGeneratorEntity


@dataclass(frozen=True, slots=True)
class GeneratorBinarySensorDescription:
    key: str
    translation_key: str


CORE_BINARY_SENSORS: tuple[GeneratorBinarySensorDescription, ...] = (
    GeneratorBinarySensorDescription(ROLE_GENERATOR_RUNNING, ROLE_GENERATOR_RUNNING),
    GeneratorBinarySensorDescription(ROLE_GENERATOR_FAULT, ROLE_GENERATOR_FAULT),
    GeneratorBinarySensorDescription(ROLE_UTILITY_AVAILABLE, ROLE_UTILITY_AVAILABLE),
    GeneratorBinarySensorDescription(ROLE_ATS_ON_GENERATOR, ROLE_ATS_ON_GENERATOR),
    GeneratorBinarySensorDescription(DERIVED_RUNNING_ON_GENERATOR, DERIVED_RUNNING_ON_GENERATOR),
    GeneratorBinarySensorDescription(DERIVED_UTILITY_OUTAGE_ACTIVE, DERIVED_UTILITY_OUTAGE_ACTIVE),
    GeneratorBinarySensorDescription(DERIVED_TRANSFER_IN_PROGRESS, DERIVED_TRANSFER_IN_PROGRESS),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        CumminsBinarySensor(coordinator, entry, description) for description in CORE_BINARY_SENSORS
    )


class CumminsBinarySensor(CumminsGeneratorEntity, BinarySensorEntity):
    """Bitmap-derived binary sensor."""

    entity_description: GeneratorBinarySensorDescription

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: GeneratorBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_translation_key = description.translation_key
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.values.get(self.entity_description.key)
        return value if isinstance(value, bool) else None

    @property
    def available(self) -> bool:
        return super().available and self.is_on is not None
