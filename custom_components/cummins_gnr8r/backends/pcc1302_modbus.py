from __future__ import annotations

from datetime import UTC, datetime

from homeassistant.core import HomeAssistant

from ..const import (
    BACKEND_PCC1302_MODBUS,
    DEFAULT_MODBUS_MODEL,
    MODBUS_REGISTER_ATS1_DEVICE_TYPE,
    MODBUS_REGISTER_ATS1_EXTENDED_BITMAP,
    MODBUS_REGISTER_ATS1_FAULT_CODE,
    MODBUS_REGISTER_ATS1_FAULT_TYPE,
    MODBUS_REGISTER_ATS1_MODE,
    MODBUS_REGISTER_ATS1_NFPA_BITMAP,
    MODBUS_REGISTER_ATS1_STATE,
    MODBUS_REGISTER_BATTERY_VOLTAGE,
    MODBUS_REGISTER_COOLANT_TEMPERATURE,
    MODBUS_REGISTER_CURRENT_FAULT_CODE,
    MODBUS_REGISTER_CURRENT_FAULT_TYPE,
    MODBUS_REGISTER_ENGINE_SPEED,
    MODBUS_REGISTER_EXTENDED_BITMAP,
    MODBUS_REGISTER_FREQUENCY,
    MODBUS_REGISTER_GENSET_LOAD_PERCENT,
    MODBUS_REGISTER_GENSET_TOTAL_KW,
    MODBUS_REGISTER_NFPA_BITMAP,
    MODBUS_REGISTER_OIL_PRESSURE,
    MODBUS_REGISTER_RUNTIME_HIGH,
    MODBUS_REGISTER_RUNTIME_LOW,
    MODBUS_REGISTER_TOTAL_RUNS,
    MODBUS_REGISTER_UTILITY_FREQUENCY,
    MODBUS_REGISTER_UTILITY_LN_AVERAGE_VOLTAGE,
    ROLE_ATS_ON_GENERATOR,
    ROLE_GENERATOR_FAULT,
    ROLE_GENERATOR_RUNNING,
    ROLE_UTILITY_AVAILABLE,
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
OPTIONAL_GROUPS: tuple[RegisterGroup, ...] = (
    RegisterGroup("current_fault", MODBUS_REGISTER_CURRENT_FAULT_CODE, 2),
    RegisterGroup("genset_load", MODBUS_REGISTER_GENSET_LOAD_PERCENT, 2),
    RegisterGroup("ats_1_status", MODBUS_REGISTER_ATS1_DEVICE_TYPE, 9),
    RegisterGroup("utility_bus", MODBUS_REGISTER_UTILITY_LN_AVERAGE_VOLTAGE, 1),
    RegisterGroup("utility_frequency", MODBUS_REGISTER_UTILITY_FREQUENCY, 1),
)

BIT_COMMON_ALARM = 15
BIT_GENSET_SUPPLYING_LOAD = 14
BIT_GENSET_RUNNING = 13
BIT_CHECK_GENSET = 15
BIT_EMERGENCY_STOP = 0
BIT_NFPA_NOT_IN_AUTO = 12
BIT_NFPA_LOW_BATTERY = 10
BIT_NFPA_CHARGER_AC_FAILURE = 9
BIT_NFPA_FAIL_TO_START = 8
BIT_NFPA_HIGH_ENGINE_TEMPERATURE = 5
BIT_NFPA_LOW_OIL_PRESSURE = 3
BIT_NFPA_OVERSPEED = 2
BIT_NFPA_LOW_FUEL = 0
BIT_EXTENDED_TEST_EXERCISE = 9
BIT_EXTENDED_LOAD_SHED = 7
BIT_EXTENDED_TRANSFER_INHIBIT = 6
BIT_EXTENDED_RETRANSFER_INHIBIT = 5
BIT_EXTENDED_FAIL_TO_CLOSE = 4
BIT_EXTENDED_FAIL_TO_DISCONNECT = 3
BIT_EXTENDED_FAIL_TO_SYNCHRONIZE = 2
BIT_EXTENDED_BYPASS_SOURCE_1 = 1
BIT_EXTENDED_BYPASS_SOURCE_2 = 0
BIT_ATS_SOURCE_1_AVAILABLE = 15
BIT_ATS_SOURCE_2_AVAILABLE = 14
BIT_ATS_SOURCE_1_CONNECTED = 13
BIT_ATS_SOURCE_2_CONNECTED = 12
BIT_ATS_COMMON_ALARM = 11

ATS_MODE_MAP = {
    0: "test",
    1: "utility_genset",
    2: "utility_utility",
    3: "genset_genset",
}
ATS_STATE_MAP = {
    0: "neutral",
    1: "source_1_connected",
    2: "source_2_connected",
    3: "source_1_and_2_connected",
}
ATS_FAULT_TYPE_MAP = {
    0: "no_faults",
    1: "warning",
}
CURRENT_FAULT_TYPE_MAP = {
    0: "none",
    1: "warning",
    2: "derate",
    3: "shutdown_with_cooldown",
    4: "shutdown",
}


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
        register_groups, group_health = await _async_read_groups(self.hass, self.client)
        values = _decode_values(register_groups)
        logical_signals = {
            ROLE_GENERATOR_RUNNING: values["modbus_genset_running"],
            ROLE_GENERATOR_FAULT: any(
                values[name]
                for name in (
                    "modbus_common_alarm",
                    "modbus_check_genset",
                    "modbus_emergency_stop",
                    "low_battery_voltage_alarm",
                    "charger_ac_failure",
                    "fail_to_start",
                    "high_engine_temperature",
                    "low_oil_pressure_alarm",
                    "overspeed",
                    "low_fuel_level",
                )
            ),
            ROLE_UTILITY_AVAILABLE: values.get("utility_available"),
            ROLE_ATS_ON_GENERATOR: values.get("ats_on_generator"),
        }
        return BackendUpdate(
            backend=self.backend_type,
            logical_signals=logical_signals,
            values=values,
            details={
                "backend_name": self.backend_name,
                "group_health": group_health,
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
) -> tuple[dict[str, dict[int, int]], dict[str, bool]]:
    """Read all configured register groups."""
    results: dict[str, dict[int, int]] = {}
    group_health: dict[str, bool] = {}
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
        group_health[group.key] = True

    for group in OPTIONAL_GROUPS:
        try:
            registers = await hass.async_add_executor_job(
                client.read_holding_registers,
                group.start_address,
                group.count,
            )
        except Exception:
            group_health[group.key] = False
            continue
        results[group.key] = {
            group.start_address + offset: value for offset, value in enumerate(registers)
        }
        group_health[group.key] = True

    return results, group_health


def _decode_values(
    register_groups: dict[str, dict[int, int]]
) -> dict[str, int | float | bool | str | None]:
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

    values: dict[str, int | float | bool | str | None] = {
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
        "not_in_auto": bit_is_set(nfpa_bitmap, BIT_NFPA_NOT_IN_AUTO),
        "low_battery_voltage_alarm": bit_is_set(nfpa_bitmap, BIT_NFPA_LOW_BATTERY),
        "charger_ac_failure": bit_is_set(nfpa_bitmap, BIT_NFPA_CHARGER_AC_FAILURE),
        "fail_to_start": bit_is_set(nfpa_bitmap, BIT_NFPA_FAIL_TO_START),
        "high_engine_temperature": bit_is_set(nfpa_bitmap, BIT_NFPA_HIGH_ENGINE_TEMPERATURE),
        "low_oil_pressure_alarm": bit_is_set(nfpa_bitmap, BIT_NFPA_LOW_OIL_PRESSURE),
        "overspeed": bit_is_set(nfpa_bitmap, BIT_NFPA_OVERSPEED),
        "low_fuel_level": bit_is_set(nfpa_bitmap, BIT_NFPA_LOW_FUEL),
        "test_exercise_in_progress": bit_is_set(extended_bitmap, BIT_EXTENDED_TEST_EXERCISE),
        "load_shed": bit_is_set(extended_bitmap, BIT_EXTENDED_LOAD_SHED),
        "transfer_inhibit_active": bit_is_set(
            extended_bitmap, BIT_EXTENDED_TRANSFER_INHIBIT
        ),
        "retransfer_inhibit_active": bit_is_set(
            extended_bitmap, BIT_EXTENDED_RETRANSFER_INHIBIT
        ),
        "fail_to_close": bit_is_set(extended_bitmap, BIT_EXTENDED_FAIL_TO_CLOSE),
        "fail_to_disconnect": bit_is_set(extended_bitmap, BIT_EXTENDED_FAIL_TO_DISCONNECT),
        "fail_to_synchronize": bit_is_set(
            extended_bitmap, BIT_EXTENDED_FAIL_TO_SYNCHRONIZE
        ),
        "bypass_to_source_1": bit_is_set(extended_bitmap, BIT_EXTENDED_BYPASS_SOURCE_1),
        "bypass_to_source_2": bit_is_set(extended_bitmap, BIT_EXTENDED_BYPASS_SOURCE_2),
    }
    values["action_required"] = any(
        values[name]
        for name in (
            "modbus_common_alarm",
            "modbus_check_genset",
            "modbus_emergency_stop",
            "not_in_auto",
            "low_battery_voltage_alarm",
            "charger_ac_failure",
            "fail_to_start",
            "high_engine_temperature",
            "low_oil_pressure_alarm",
            "overspeed",
            "low_fuel_level",
            "fail_to_close",
            "fail_to_disconnect",
            "fail_to_synchronize",
        )
    )
    values.update(_decode_optional_fault_and_load_values(registers))
    values.update(_decode_optional_ats_values(registers))
    values.update(_decode_optional_utility_values(registers))
    values["action_required"] = bool(
        values["action_required"] or values.get("ats_common_alarm", False)
    )
    return values


def _decode_optional_ats_values(registers: dict[int, int]) -> dict[str, int | bool | str | None]:
    """Decode ATS/utility state when ATS registers are present."""
    if (
        MODBUS_REGISTER_ATS1_MODE not in registers
        or MODBUS_REGISTER_ATS1_EXTENDED_BITMAP not in registers
    ):
        return {
            "ats_mode": None,
            "ats_state": None,
            "ats_fault_code": None,
            "ats_fault_type": None,
            "raw_ats_nfpa_bitmap": None,
            "raw_ats_extended_bitmap": None,
            "source_1_available": None,
            "source_2_available": None,
            "source_1_connected": None,
            "source_2_connected": None,
            "ats_common_alarm": None,
            "utility_available": None,
            "ats_on_generator": None,
        }

    ats_mode_raw = registers[MODBUS_REGISTER_ATS1_MODE]
    ats_state_raw = registers[MODBUS_REGISTER_ATS1_STATE]
    ats_fault_type_raw = registers[MODBUS_REGISTER_ATS1_FAULT_TYPE]
    ats_nfpa = registers[MODBUS_REGISTER_ATS1_NFPA_BITMAP]
    ats_extended = registers[MODBUS_REGISTER_ATS1_EXTENDED_BITMAP]

    source_1_available = bit_is_set(ats_extended, BIT_ATS_SOURCE_1_AVAILABLE)
    source_2_available = bit_is_set(ats_extended, BIT_ATS_SOURCE_2_AVAILABLE)
    source_1_connected = bit_is_set(ats_extended, BIT_ATS_SOURCE_1_CONNECTED)
    source_2_connected = bit_is_set(ats_extended, BIT_ATS_SOURCE_2_CONNECTED)

    utility_available: bool | None = None
    ats_on_generator: bool | None = None
    if ats_mode_raw == 1:
        utility_available = source_1_available
        ats_on_generator = source_2_connected

    return {
        "ats_mode": ATS_MODE_MAP.get(ats_mode_raw, f"unknown_{ats_mode_raw}"),
        "ats_state": ATS_STATE_MAP.get(ats_state_raw, f"unknown_{ats_state_raw}"),
        "ats_fault_code": registers[MODBUS_REGISTER_ATS1_FAULT_CODE],
        "ats_fault_type": ATS_FAULT_TYPE_MAP.get(
            ats_fault_type_raw, f"unknown_{ats_fault_type_raw}"
        ),
        "raw_ats_nfpa_bitmap": ats_nfpa,
        "raw_ats_extended_bitmap": ats_extended,
        "source_1_available": source_1_available,
        "source_2_available": source_2_available,
        "source_1_connected": source_1_connected,
        "source_2_connected": source_2_connected,
        "ats_common_alarm": bit_is_set(ats_extended, BIT_ATS_COMMON_ALARM),
        "utility_available": utility_available,
        "ats_on_generator": ats_on_generator,
    }


def _decode_optional_utility_values(registers: dict[int, int]) -> dict[str, float | None]:
    """Decode optional utility-bus measurements when exposed by the endpoint."""
    utility_ln_average_voltage = registers.get(MODBUS_REGISTER_UTILITY_LN_AVERAGE_VOLTAGE)
    utility_frequency = registers.get(MODBUS_REGISTER_UTILITY_FREQUENCY)
    return {
        "utility_ln_average_voltage": float(utility_ln_average_voltage)
        if utility_ln_average_voltage is not None
        else None,
        "utility_frequency": round(utility_frequency * 0.1, 1)
        if utility_frequency is not None
        else None,
    }


def _decode_optional_fault_and_load_values(
    registers: dict[int, int],
) -> dict[str, int | float | str | None]:
    """Decode optional current-fault and load registers."""
    fault_code = registers.get(MODBUS_REGISTER_CURRENT_FAULT_CODE)
    fault_type = registers.get(MODBUS_REGISTER_CURRENT_FAULT_TYPE)
    load_percent = registers.get(MODBUS_REGISTER_GENSET_LOAD_PERCENT)
    total_kw = registers.get(MODBUS_REGISTER_GENSET_TOTAL_KW)
    return {
        "current_fault_code": fault_code,
        "current_fault_type": CURRENT_FAULT_TYPE_MAP.get(fault_type, f"unknown_{fault_type}")
        if fault_type is not None
        else None,
        "genset_load_percent": round(load_percent * 0.5, 1)
        if load_percent is not None
        else None,
        "genset_total_kw": float(total_kw) if total_kw is not None else None,
    }


def decode_u32(high_word: int, low_word: int) -> int:
    """Combine two 16-bit words into a 32-bit integer."""
    return (high_word << 16) | low_word


def bit_is_set(register_value: int, bit: int) -> bool:
    """Return True when a bitmap bit is set."""
    return bool(register_value & (1 << bit))
