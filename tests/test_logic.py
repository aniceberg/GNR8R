from __future__ import annotations

from custom_components.cummins_gnr8r.const import (
    DERIVED_RUNNING_ON_GENERATOR,
    DERIVED_TRANSFER_IN_PROGRESS,
    DERIVED_UTILITY_OUTAGE_ACTIVE,
    ROLE_ATS_ON_GENERATOR,
    ROLE_GENERATOR_FAULT,
    ROLE_GENERATOR_RUNNING,
    ROLE_UTILITY_AVAILABLE,
    STATE_TEXT_KEY,
)
from custom_components.cummins_gnr8r.coordinator import _synthesize_values
from custom_components.cummins_gnr8r.status import decode_operating_status


def test_state_synthesis_normal_utility() -> None:
    values = _synthesize_values(
        {
            ROLE_UTILITY_AVAILABLE: True,
            ROLE_ATS_ON_GENERATOR: False,
            ROLE_GENERATOR_RUNNING: False,
            ROLE_GENERATOR_FAULT: False,
        }
    )
    assert values[DERIVED_RUNNING_ON_GENERATOR] is False
    assert values[DERIVED_TRANSFER_IN_PROGRESS] is False
    assert values[DERIVED_UTILITY_OUTAGE_ACTIVE] is False
    assert values[STATE_TEXT_KEY] == "Normal utility power"


def test_state_synthesis_running_on_generator_with_fault() -> None:
    values = _synthesize_values(
        {
            ROLE_UTILITY_AVAILABLE: False,
            ROLE_ATS_ON_GENERATOR: True,
            ROLE_GENERATOR_RUNNING: True,
            ROLE_GENERATOR_FAULT: True,
        }
    )
    assert values[DERIVED_RUNNING_ON_GENERATOR] is True
    assert values[DERIVED_TRANSFER_IN_PROGRESS] is False
    assert values[DERIVED_UTILITY_OUTAGE_ACTIVE] is True
    assert values[STATE_TEXT_KEY] == "Running on generator - Fault active"


def test_state_synthesis_transition_unknown() -> None:
    values = _synthesize_values(
        {
            ROLE_UTILITY_AVAILABLE: None,
            ROLE_ATS_ON_GENERATOR: True,
            ROLE_GENERATOR_RUNNING: True,
            ROLE_GENERATOR_FAULT: False,
        }
    )
    assert values[DERIVED_RUNNING_ON_GENERATOR] is None
    assert values[DERIVED_TRANSFER_IN_PROGRESS] is None
    assert values[STATE_TEXT_KEY] == "Transition / unknown"


def test_operating_status_precedence_fault_over_running() -> None:
    values = decode_operating_status(
        {
            ROLE_GENERATOR_RUNNING: True,
            ROLE_GENERATOR_FAULT: True,
            "not_in_auto": True,
        }
    )
    assert values["generator_operating_status"] == "Fault"
    assert values["action_required"] is True


def test_operating_status_not_in_auto_before_running() -> None:
    values = decode_operating_status(
        {
            ROLE_GENERATOR_RUNNING: True,
            ROLE_GENERATOR_FAULT: False,
            "not_in_auto": True,
        }
    )
    assert values["generator_operating_status"] == "Not in auto"


def test_operating_status_stopped_and_unknown() -> None:
    assert decode_operating_status(
        {ROLE_GENERATOR_RUNNING: False, ROLE_GENERATOR_FAULT: False}
    )["generator_operating_status"] == "Stopped"
    assert decode_operating_status(
        {ROLE_GENERATOR_RUNNING: None, ROLE_GENERATOR_FAULT: False}
    )["generator_operating_status"] == "Transition / unknown"
