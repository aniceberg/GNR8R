from __future__ import annotations

from typing import Final

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import EntityCategory, UnitOfFrequency, UnitOfPressure, UnitOfTemperature

from .const import (
    REGISTER_BATTERY_VOLTAGE,
    REGISTER_BITMAP_1,
    REGISTER_BITMAP_2,
    REGISTER_COOLANT_TEMPERATURE,
    REGISTER_ENGINE_SPEED,
    REGISTER_LINE_FREQUENCY,
    REGISTER_OIL_PRESSURE,
    REGISTER_TOTAL_RUNS,
)
from .models import (
    BinarySensorDescription,
    BitmapSensorDescription,
    RegisterGroup,
    SensorDescription,
)

REGISTER_GROUPS: Final[tuple[RegisterGroup, ...]] = (
    RegisterGroup(key="nfpa_status", start_address=REGISTER_BITMAP_1, count=2),
    RegisterGroup(key="line_frequency", start_address=REGISTER_LINE_FREQUENCY, count=1),
    RegisterGroup(key="engine_metrics", start_address=REGISTER_BATTERY_VOLTAGE, count=9),
)

SENSOR_TYPES: Final[tuple[SensorDescription, ...]] = (
    SensorDescription(
        key="average_line_frequency",
        name="Average line frequency",
        register=REGISTER_LINE_FREQUENCY,
        scale=0.1,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        suggested_display_precision=1,
    ),
    SensorDescription(
        key="battery_voltage",
        name="Battery voltage",
        register=REGISTER_BATTERY_VOLTAGE,
        scale=0.1,
        native_unit_of_measurement="V",
        device_class=SensorDeviceClass.VOLTAGE,
        suggested_display_precision=1,
    ),
    SensorDescription(
        key="oil_pressure",
        name="Oil pressure",
        register=REGISTER_OIL_PRESSURE,
        native_unit_of_measurement=UnitOfPressure.KPA,
        device_class=SensorDeviceClass.PRESSURE,
    ),
    SensorDescription(
        key="coolant_temperature",
        name="Coolant temperature",
        register=REGISTER_COOLANT_TEMPERATURE,
        scale=0.1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        suggested_display_precision=1,
    ),
    SensorDescription(
        key="engine_speed",
        name="Engine speed",
        register=REGISTER_ENGINE_SPEED,
        native_unit_of_measurement="rpm",
    ),
    SensorDescription(
        key="total_runs",
        name="Total runs",
        register=REGISTER_TOTAL_RUNS,
        native_unit_of_measurement="runs",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

BITMAP_SENSOR_TYPES: Final[tuple[BitmapSensorDescription, ...]] = (
    BitmapSensorDescription(
        key="raw_nfpa_bitmap_1",
        name="Raw NFPA bitmap 1",
        register=REGISTER_BITMAP_1,
    ),
    BitmapSensorDescription(
        key="raw_nfpa_bitmap_2",
        name="Raw NFPA bitmap 2",
        register=REGISTER_BITMAP_2,
    ),
)

BINARY_SENSOR_TYPES: Final[tuple[BinarySensorDescription, ...]] = (
    BinarySensorDescription(
        key="common_alarm",
        name="Common alarm",
        register=REGISTER_BITMAP_1,
        bit=15,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="genset_supplying_load",
        name="Genset supplying load",
        register=REGISTER_BITMAP_1,
        bit=14,
    ),
    BinarySensorDescription(
        key="genset_running",
        name="Genset running",
        register=REGISTER_BITMAP_1,
        bit=13,
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorDescription(
        key="not_in_auto",
        name="Not in auto",
        register=REGISTER_BITMAP_1,
        bit=12,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="low_battery_voltage_alarm",
        name="Low battery voltage alarm",
        register=REGISTER_BITMAP_1,
        bit=10,
        device_class=BinarySensorDeviceClass.BATTERY,
    ),
    BinarySensorDescription(
        key="charger_ac_failure",
        name="Charger AC failure",
        register=REGISTER_BITMAP_1,
        bit=9,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="fail_to_start",
        name="Fail to start",
        register=REGISTER_BITMAP_1,
        bit=8,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="high_engine_temperature",
        name="High engine temperature",
        register=REGISTER_BITMAP_1,
        bit=5,
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    BinarySensorDescription(
        key="low_oil_pressure",
        name="Low oil pressure",
        register=REGISTER_BITMAP_1,
        bit=3,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="overspeed",
        name="Overspeed",
        register=REGISTER_BITMAP_1,
        bit=2,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="low_fuel_level",
        name="Low fuel level",
        register=REGISTER_BITMAP_1,
        bit=0,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="check_genset",
        name="Check genset",
        register=REGISTER_BITMAP_2,
        bit=15,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="ground_fault",
        name="Ground fault",
        register=REGISTER_BITMAP_2,
        bit=14,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="high_ac_voltage",
        name="High AC voltage",
        register=REGISTER_BITMAP_2,
        bit=13,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="low_ac_voltage",
        name="Low AC voltage",
        register=REGISTER_BITMAP_2,
        bit=12,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="under_frequency",
        name="Under frequency",
        register=REGISTER_BITMAP_2,
        bit=11,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="overload",
        name="Overload",
        register=REGISTER_BITMAP_2,
        bit=10,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="overcurrent",
        name="Overcurrent",
        register=REGISTER_BITMAP_2,
        bit=9,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="short_circuit",
        name="Short circuit",
        register=REGISTER_BITMAP_2,
        bit=8,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorDescription(
        key="emergency_stop",
        name="Emergency stop",
        register=REGISTER_BITMAP_2,
        bit=0,
        device_class=BinarySensorDeviceClass.SAFETY,
    ),
)

ALL_DEFINED_REGISTERS: Final[set[int]] = {
    *(description.register for description in SENSOR_TYPES),
    *(description.register for description in BITMAP_SENSOR_TYPES),
}


def register_to_offset(register: int) -> int:
    """Convert a 4xxxx holding register to a zero-based Modbus offset."""
    return register - 40001


def scale_register_value(raw_value: int, scale: float) -> int | float:
    """Scale a raw register value for Home Assistant."""
    if scale == 1:
        return raw_value
    return round(raw_value * scale, 3)


def bit_is_set(register_value: int, bit: int) -> bool:
    """Return True if a bit is set in a 16-bit bitmap."""
    return bool(register_value & (1 << bit))
