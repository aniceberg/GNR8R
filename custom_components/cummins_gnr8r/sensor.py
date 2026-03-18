from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfFrequency, UnitOfPressure, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import BACKEND_PCC1302_MODBUS, DATA_COORDINATOR, DOMAIN
from .entity import CumminsGeneratorEntity
from .text_sensor import CumminsStateTextSensor


@dataclass(frozen=True, slots=True)
class GeneratorSensorDescription:
    key: str
    translation_key: str
    native_unit_of_measurement: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    entity_category: EntityCategory | None = None
    suggested_display_precision: int | None = None


MODBUS_SENSORS: tuple[GeneratorSensorDescription, ...] = (
    GeneratorSensorDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        native_unit_of_measurement="V",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    GeneratorSensorDescription(
        key="oil_pressure",
        translation_key="oil_pressure",
        native_unit_of_measurement=UnitOfPressure.KPA,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    GeneratorSensorDescription(
        key="coolant_temperature_c",
        translation_key="coolant_temperature_c",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    GeneratorSensorDescription(
        key="coolant_temperature_f",
        translation_key="coolant_temperature_f",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    GeneratorSensorDescription(
        key="engine_speed",
        translation_key="engine_speed",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    GeneratorSensorDescription(
        key="total_runs",
        translation_key="total_runs",
        native_unit_of_measurement="runs",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    GeneratorSensorDescription(
        key="engine_runtime",
        translation_key="engine_runtime",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    GeneratorSensorDescription(
        key="frequency",
        translation_key="frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    GeneratorSensorDescription(
        key="raw_nfpa_bitmap",
        translation_key="raw_nfpa_bitmap",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    GeneratorSensorDescription(
        key="raw_extended_bitmap",
        translation_key="raw_extended_bitmap",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities: list[SensorEntity] = [CumminsStateTextSensor(coordinator, entry)]
    if coordinator.data.backend == BACKEND_PCC1302_MODBUS:
        entities.extend(
            CumminsSensor(coordinator, entry, description) for description in MODBUS_SENSORS
        )
    async_add_entities(entities)


class CumminsSensor(CumminsGeneratorEntity, SensorEntity):
    """Backend-provided generator sensor."""

    entity_description: GeneratorSensorDescription

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: GeneratorSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_translation_key = description.translation_key
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
