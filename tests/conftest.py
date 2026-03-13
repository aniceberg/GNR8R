from __future__ import annotations

import sys
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.cummins_generator.const import (
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_PARITY,
    CONF_POLL_INTERVAL,
    CONF_SCAN_THROTTLE_MS,
    CONF_SERIAL_PORT,
    CONF_SLAVE,
    CONF_STOPBITS,
)


@pytest.fixture
def entry_data() -> dict[str, int | str]:
    return {
        CONF_SERIAL_PORT: "/dev/ttyUSB0",
        CONF_SLAVE: 1,
        CONF_BAUDRATE: 9600,
        CONF_BYTESIZE: 8,
        CONF_PARITY: "N",
        CONF_STOPBITS: 1,
        CONF_POLL_INTERVAL: 10,
        CONF_SCAN_THROTTLE_MS: 0,
    }


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations) -> None:
    """Enable loading the integration from this repository during tests."""


@pytest.fixture
def mock_probe() -> Generator:
    with patch(
        "custom_components.cummins_generator.config_flow.CumminsModbusClient.probe",
        return_value={40061: 123, 40068: 1800},
    ) as probe:
        yield probe


@pytest.fixture
def config_entry(hass, entry_data):
    entry = MockConfigEntry(
        domain="cummins_generator",
        title="Cummins Generator",
        data=entry_data,
        unique_id="/dev/ttyUSB0:1",
    )
    entry.add_to_hass(hass)
    return entry
