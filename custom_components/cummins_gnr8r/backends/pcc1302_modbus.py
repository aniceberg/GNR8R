from __future__ import annotations

from datetime import UTC, datetime

from homeassistant.core import HomeAssistant

from ..const import (
    BACKEND_PCC1302_MODBUS,
    DEFAULT_MODBUS_MODEL,
    MODBUS_REGISTER_BATTERY_VOLTAGE,
    MODBUS_REGISTER_COOLANT_TEMPERATURE,
    MODBUS_REGISTER_ENGINE_SPEED,
    MODBUS_REGISTER_EXTENDED_BITMAP,
    MODBUS_REGISTER_FREQUENCY,
    MODBUS_REGISTER_NFPA_BITMAP,
    MODBUS_REGISTER_OIL_PRESSURE,
    MODBUS_REGISTER_RUNTIME_HIGH,
    MODBUS_REGISTER_RUNTIME_LOW,
    MODBUS_REGISTER_TOTAL_RUNS,
    ROLE_GENERATOR_FAULT,
    ROLE_GENERATOR_RUNNING,
)
from ..modbus_client import CumminsModbusClient
from ..models import BackendUpdate, RegisterGroup
from .base import CumminsBackendError

PCC1302_GROUPS: tuple[RegisterGroup, ...] = (
    RegisterGroup("status", MODBUS_REGISTER_NFPA_BITMAP, 2),
    RegisterGroup("metrics_a", MODBUS_REGISTER_BATTERY_VOLTAGE, 4),
    RegisterGroup("metrics_b", MODBUS_REGISTER_ENGINE_SPEED, 4),
    RegisterGroup("frequency", MODBUS_REGISTER_FREQUENCY, 1),
)

BIT_COMMON_ALARM = 15
BIT_GENSET_SUPPLYING_LOAD = 14
BIT_GENSET_RUNNING = 13
BIT_CHECK_GENSET = 15
BIT_EMERGENCY_STOP = 0


class PCC1302ModbusBackend:
    """PowerCommand 2.x backend over Modbus RTU."""

    backend_type = BACKEND_PCC1302_MODBUS
    backend_name = "PCC1302 Modbus"
    device_model = DEFAULT_MODBUS_MODEL

    def __init__(self, hass: HomeAssistant, client: CumminsModbusClient) -> None:
        self.hass = hass
        self.client = client
        self.source_identifier = f"{client.params.port}:{client.params.slave}"

    async def async_fetch(self) -> BackendUpdate:
        """Fetch PCC1302 values from Modbus."""
        register_groups = await _async_read_groups(self.hass, self.client)
        values = _decode_values(register_groups)
        logical_signals = {
            ROLE_GENERATOR_RUNNING: values["modbus_genset_running"],
            ROLE_GENERATOR_FAULT: any(
                values[name]
                for name in ("modbus_common_alarm", "modbus_check_genset", "modbus_emergency_stop")
            ),
            "utility_available": None,
            "ats_on_generator": None,
        }
        return BackendUpdate(
            backend=self.backend_type,
            logical_signals=logical_signals,
            values=values,
            details={
                "backend_name": self.backend_name,
                "group_health": dict.fromkeys(register_groups, True),
                "source": self.source_identifier,
            },
            fetched_at=datetime.now(UTC),
        )


async def async_validate_modbus_backend(hass: HomeAssistant, client: CumminsModbusClient) -> None:
    """Validate that Modbus connectivity works against safe PCC1302 registers."""
    await hass.async_add_executor_job(
        client.probe,
        (MODBUS_REGISTER_BATTERY_VOLTAGE, MODBUS_REGISTER_ENGINE_SPEED),
    )


async def _async_read_groups(
    hass: HomeAssistant, client: CumminsModbusClient
) -> dict[str, dict[int, int]]:
    """Read all configured register groups."""
    results: dict[str, dict[int, int]] = {}
    for group in PCC1302_GROUPS:
        try:
            registers = await hass.async_add_executor_job(
                client.read_holding_registers,
                group.start_address,
                group.count,
            )
        except Exception as err:  # pragma: no cover - translated by client in normal paths
            raise CumminsBackendError(str(err)) from err
        results[group.key] = {
            group.start_address + offset: value for offset, value in enumerate(registers)
        }
    return results


def _decode_values(register_groups: dict[str, dict[int, int]]) -> dict[str, int | float | bool]:
    """Decode raw PCC1302 registers into integration values."""
    registers = {
        register: value
        for group_values in register_groups.values()
        for register, value in group_values.items()
    }
    nfpa_bitmap = registers[MODBUS_REGISTER_NFPA_BITMAP]
    extended_bitmap = registers[MODBUS_REGISTER_EXTENDED_BITMAP]
    coolant_kelvin = registers[MODBUS_REGISTER_COOLANT_TEMPERATURE] * 0.1
    coolant_c = round(coolant_kelvin - 273.15, 1)
    coolant_f = round((coolant_c * 9 / 5) + 32, 1)
    runtime_raw = decode_u32(
        registers[MODBUS_REGISTER_RUNTIME_HIGH],
        registers[MODBUS_REGISTER_RUNTIME_LOW],
    )

    return {
        "battery_voltage": round(registers[MODBUS_REGISTER_BATTERY_VOLTAGE] * 0.1, 1),
        "oil_pressure": round(registers[MODBUS_REGISTER_OIL_PRESSURE] * 0.1, 1),
        "coolant_temperature_c": coolant_c,
        "coolant_temperature_f": coolant_f,
        "engine_speed": registers[MODBUS_REGISTER_ENGINE_SPEED],
        "total_runs": registers[MODBUS_REGISTER_TOTAL_RUNS],
        "engine_runtime": runtime_raw,
        "frequency": round(registers[MODBUS_REGISTER_FREQUENCY] * 0.1, 1),
        "raw_nfpa_bitmap": nfpa_bitmap,
        "raw_extended_bitmap": extended_bitmap,
        "modbus_common_alarm": bit_is_set(nfpa_bitmap, BIT_COMMON_ALARM),
        "modbus_genset_supplying_load": bit_is_set(nfpa_bitmap, BIT_GENSET_SUPPLYING_LOAD),
        "modbus_genset_running": bit_is_set(nfpa_bitmap, BIT_GENSET_RUNNING),
        "modbus_check_genset": bit_is_set(extended_bitmap, BIT_CHECK_GENSET),
        "modbus_emergency_stop": bit_is_set(extended_bitmap, BIT_EMERGENCY_STOP),
    }


def decode_u32(high_word: int, low_word: int) -> int:
    """Combine two 16-bit words into a 32-bit integer."""
    return (high_word << 16) | low_word


def bit_is_set(register_value: int, bit: int) -> bool:
    """Return True when a bitmap bit is set."""
    return bool(register_value & (1 << bit))
