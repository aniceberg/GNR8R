from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.cummins_gnr8r.const import (
    BACKEND_ESPHOME_DISCRETE,
    CONF_ATS_ON_GENERATOR_ENTITY_ID,
    CONF_BACKEND,
    CONF_GENERATOR_FAULT_ENTITY_ID,
    CONF_GENERATOR_RUNNING_ENTITY_ID,
    CONF_INVERT_ATS_ON_GENERATOR,
    CONF_INVERT_GENERATOR_FAULT,
    CONF_INVERT_GENERATOR_RUNNING,
    CONF_INVERT_UTILITY_AVAILABLE,
    CONF_POLL_INTERVAL,
    CONF_SCAN_THROTTLE_MS,
    CONF_UTILITY_AVAILABLE_ENTITY_ID,
)


@pytest.fixture
def discrete_entry_data() -> dict[str, int | str | bool]:
    return {
        CONF_BACKEND: BACKEND_ESPHOME_DISCRETE,
        CONF_UTILITY_AVAILABLE_ENTITY_ID: "binary_sensor.utility_available",
        CONF_ATS_ON_GENERATOR_ENTITY_ID: "binary_sensor.ats_on_generator",
        CONF_GENERATOR_RUNNING_ENTITY_ID: "binary_sensor.generator_running_input",
        CONF_GENERATOR_FAULT_ENTITY_ID: "binary_sensor.generator_fault_input",
        CONF_INVERT_UTILITY_AVAILABLE: False,
        CONF_INVERT_ATS_ON_GENERATOR: False,
        CONF_INVERT_GENERATOR_RUNNING: False,
        CONF_INVERT_GENERATOR_FAULT: False,
        CONF_POLL_INTERVAL: 10,
        CONF_SCAN_THROTTLE_MS: 0,
    }


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations) -> None:
    """Enable loading the integration from this repository during tests."""


@pytest.fixture
def config_entry(hass, discrete_entry_data):
    entry = MockConfigEntry(
        domain="cummins_gnr8r",
        title="cummins_GNR8R",
        data=discrete_entry_data,
        unique_id="discrete:test",
    )
    entry.add_to_hass(hass)
    return entry
