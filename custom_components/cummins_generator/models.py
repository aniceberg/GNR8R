from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import EntityCategory


@dataclass(frozen=True, slots=True)
class RegisterGroup:
    key: str
    start_address: int
    count: int


@dataclass(frozen=True, slots=True)
class SensorDescription:
    key: str
    name: str
    register: int
    scale: float = 1.0
    native_unit_of_measurement: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    entity_category: EntityCategory | None = None
    suggested_display_precision: int | None = None
    enabled_by_default: bool = True


@dataclass(frozen=True, slots=True)
class BitmapSensorDescription:
    key: str
    name: str
    register: int
    entity_category: EntityCategory | None = EntityCategory.DIAGNOSTIC


@dataclass(frozen=True, slots=True)
class BinarySensorDescription:
    key: str
    name: str
    register: int
    bit: int
    device_class: BinarySensorDeviceClass | None = None
    entity_category: EntityCategory | None = None
    enabled_by_default: bool = True


@dataclass(slots=True)
class CoordinatorSnapshot:
    values: dict[str, Any]
    register_availability: dict[int, bool]
    group_health: dict[str, bool]
    fetched_at: datetime
