from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cummins_generator.const import DOMAIN


@pytest.mark.asyncio
async def test_setup_entry_failure_bubbles_up(hass, entry_data) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Cummins Generator",
        data=entry_data,
        unique_id="/dev/ttyUSB0:1",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.cummins_generator.coordinator.CumminsGeneratorCoordinator.async_config_entry_first_refresh",
        side_effect=UpdateFailed("failed"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id) is False
