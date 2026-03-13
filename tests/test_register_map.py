from __future__ import annotations

from custom_components.cummins_generator.register_map import (
    bit_is_set,
    register_to_offset,
    scale_register_value,
)


def test_register_to_offset() -> None:
    assert register_to_offset(40001) == 0
    assert register_to_offset(40016) == 15
    assert register_to_offset(40069) == 68


def test_scale_register_value() -> None:
    assert scale_register_value(600, 0.1) == 60.0
    assert scale_register_value(87, 1) == 87


def test_bit_is_set() -> None:
    value = 0b1010
    assert bit_is_set(value, 3) is True
    assert bit_is_set(value, 2) is False
    assert bit_is_set(value, 1) is True
