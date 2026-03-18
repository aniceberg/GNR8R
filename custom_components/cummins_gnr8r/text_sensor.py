from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry

from .const import STATE_TEXT_KEY
from .entity import CumminsGeneratorEntity


class CumminsStateTextSensor(CumminsGeneratorEntity, SensorEntity):
    """Text sensor showing the synthesized system state."""

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_translation_key = STATE_TEXT_KEY
        self._attr_unique_id = f"{entry.entry_id}_{STATE_TEXT_KEY}"
        self._attr_icon = "mdi:generator-mobile"

    @property
    def native_value(self) -> str | None:
        value = self.coordinator.data.values.get(STATE_TEXT_KEY)
        return value if isinstance(value, str) else None

    @property
    def available(self) -> bool:
        return super().available and self.native_value is not None
