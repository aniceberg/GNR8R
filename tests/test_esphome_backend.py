from __future__ import annotations

import pytest

from custom_components.cummins_gnr8r.backends.esphome_discrete import (
    ESPHomeDiscreteBackend,
    async_validate_entity_mappings,
    build_discrete_mappings,
)
from custom_components.cummins_gnr8r.const import (
    CONF_ATS_ON_GENERATOR_ENTITY_ID,
    CONF_GENERATOR_FAULT_ENTITY_ID,
    CONF_GENERATOR_RUNNING_ENTITY_ID,
    CONF_INVERT_UTILITY_AVAILABLE,
    CONF_UTILITY_AVAILABLE_ENTITY_ID,
    ROLE_GENERATOR_RUNNING,
    ROLE_UTILITY_AVAILABLE,
)
from custom_components.cummins_gnr8r.status import decode_operating_status


@pytest.mark.asyncio
async def test_discrete_backend_applies_inversion(hass, discrete_entry_data) -> None:
    hass.states.async_set("binary_sensor.utility_available", "on")
    hass.states.async_set("binary_sensor.ats_on_generator", "off")
    hass.states.async_set("binary_sensor.generator_running_input", "off")
    hass.states.async_set("binary_sensor.generator_fault_input", "off")

    backend = ESPHomeDiscreteBackend(
        hass,
        build_discrete_mappings(
            {
                **discrete_entry_data,
                CONF_INVERT_UTILITY_AVAILABLE: True,
            }
        ),
    )
    update = await backend.async_fetch()

    assert update.logical_signals[ROLE_UTILITY_AVAILABLE] is False
    assert update.logical_signals[ROLE_GENERATOR_RUNNING] is False

    status = decode_operating_status(update.logical_signals)
    assert status["generator_operating_status"] == "Stopped"


@pytest.mark.asyncio
async def test_discrete_backend_returns_none_for_unavailable_state(
    hass, discrete_entry_data
) -> None:
    hass.states.async_set("binary_sensor.utility_available", "unavailable")
    hass.states.async_set("binary_sensor.ats_on_generator", "off")
    hass.states.async_set("binary_sensor.generator_running_input", "on")
    hass.states.async_set("binary_sensor.generator_fault_input", "off")

    backend = ESPHomeDiscreteBackend(hass, build_discrete_mappings(discrete_entry_data))
    update = await backend.async_fetch()

    assert update.logical_signals[ROLE_UTILITY_AVAILABLE] is None


@pytest.mark.asyncio
async def test_validate_discrete_entities(hass, discrete_entry_data) -> None:
    for entity_id in (
        discrete_entry_data[CONF_UTILITY_AVAILABLE_ENTITY_ID],
        discrete_entry_data[CONF_ATS_ON_GENERATOR_ENTITY_ID],
        discrete_entry_data[CONF_GENERATOR_RUNNING_ENTITY_ID],
        discrete_entry_data[CONF_GENERATOR_FAULT_ENTITY_ID],
    ):
        hass.states.async_set(entity_id, "off")

    await async_validate_entity_mappings(hass, build_discrete_mappings(discrete_entry_data))
