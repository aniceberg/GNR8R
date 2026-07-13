from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    ACTION_REQUIRED_KEY,
    BACKEND_PCC1302_MODBUS,
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
    GeneratorBinarySensorDescription(ACTION_REQUIRED_KEY, ACTION_REQUIRED_KEY),
)

MODBUS_BINARY_SENSORS: tuple[GeneratorBinarySensorDescription, ...] = (
    GeneratorBinarySensorDescription("not_in_auto", "not_in_auto"),
    GeneratorBinarySensorDescription("low_battery_voltage_alarm", "low_battery_voltage_alarm"),
    GeneratorBinarySensorDescription("charger_ac_failure", "charger_ac_failure"),
    GeneratorBinarySensorDescription("fail_to_start", "fail_to_start"),
    GeneratorBinarySensorDescription("high_engine_temperature", "high_engine_temperature"),
    GeneratorBinarySensorDescription("low_oil_pressure_alarm", "low_oil_pressure_alarm"),
    GeneratorBinarySensorDescription("overspeed", "overspeed"),
    GeneratorBinarySensorDescription("low_fuel_level", "low_fuel_level"),
    GeneratorBinarySensorDescription("test_exercise_in_progress", "test_exercise_in_progress"),
    GeneratorBinarySensorDescription("load_shed", "load_shed"),
    GeneratorBinarySensorDescription("fail_to_close", "fail_to_close"),
    GeneratorBinarySensorDescription("fail_to_disconnect", "fail_to_disconnect"),
    GeneratorBinarySensorDescription("fail_to_synchronize", "fail_to_synchronize"),
    GeneratorBinarySensorDescription("bypass_to_source_1", "bypass_to_source_1"),
    GeneratorBinarySensorDescription("bypass_to_source_2", "bypass_to_source_2"),
    GeneratorBinarySensorDescription("source_1_available", "source_1_available"),
    GeneratorBinarySensorDescription("source_2_available", "source_2_available"),
    GeneratorBinarySensorDescription("source_1_connected", "source_1_connected"),
    GeneratorBinarySensorDescription("source_2_connected", "source_2_connected"),
    GeneratorBinarySensorDescription("ats_common_alarm", "ats_common_alarm"),
    GeneratorBinarySensorDescription("transfer_inhibit_active", "transfer_inhibit_active"),
    GeneratorBinarySensorDescription("retransfer_inhibit_active", "retransfer_inhibit_active"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = [
        CumminsBinarySensor(coordinator, entry, description) for description in CORE_BINARY_SENSORS
    ]
    if coordinator.data.backend == BACKEND_PCC1302_MODBUS:
        entities.extend(
            CumminsBinarySensor(coordinator, entry, description)
            for description in MODBUS_BINARY_SENSORS
        )
    async_add_entities(entities)


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
