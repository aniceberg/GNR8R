from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ConnectionException, ModbusException
from pymodbus.pdu.exceptionresponse import ExceptionResponse

from .const import DEFAULT_RETRIES, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class CumminsGeneratorError(Exception):
    """Base integration exception."""


class SerialConnectionError(CumminsGeneratorError):
    """Raised when the serial device cannot be opened."""


class ModbusReadError(CumminsGeneratorError):
    """Raised when a Modbus read fails."""


class ModbusTimeoutError(CumminsGeneratorError):
    """Raised when a Modbus request times out."""


@dataclass(frozen=True, slots=True)
class SerialConnectionParams:
    port: str
    slave: int
    baudrate: int
    bytesize: int
    parity: str
    stopbits: int
    poll_interval: int
    scan_throttle_ms: int = 0
    timeout: float = DEFAULT_TIMEOUT
    retries: int = DEFAULT_RETRIES


class CumminsModbusClient:
    """Small sync Modbus wrapper intended for executor use."""

    def __init__(self, params: SerialConnectionParams) -> None:
        self._params = params

    @property
    def params(self) -> SerialConnectionParams:
        return self._params

    def read_holding_registers(self, start_register: int, count: int) -> list[int]:
        """Read holding registers from the configured slave."""
        last_error: Exception | None = None

        for attempt in range(1, self._params.retries + 2):
            try:
                registers = self._read_once(start_register, count)
            except ModbusTimeoutError as err:
                last_error = err
                _LOGGER.debug(
                    "Timeout reading registers %s-%s on attempt %s",
                    start_register,
                    start_register + count - 1,
                    attempt,
                )
            except (SerialConnectionError, ModbusReadError) as err:
                last_error = err
                _LOGGER.debug(
                    "Read failure for registers %s-%s on attempt %s: %s",
                    start_register,
                    start_register + count - 1,
                    attempt,
                    err,
                )
            else:
                if self._params.scan_throttle_ms:
                    time.sleep(self._params.scan_throttle_ms / 1000)
                return registers

        if last_error is None:
            raise ModbusReadError("Unknown Modbus read error")
        raise last_error

    def probe(self, registers: tuple[int, ...]) -> dict[int, int]:
        """Validate connectivity by reading a small set of known-safe registers."""
        values: dict[int, int] = {}
        for register in registers:
            values[register] = self.read_holding_registers(register, 1)[0]
        return values

    def _read_once(self, start_register: int, count: int) -> list[int]:
        client = ModbusSerialClient(
            port=self._params.port,
            baudrate=self._params.baudrate,
            bytesize=self._params.bytesize,
            parity=self._params.parity,
            stopbits=self._params.stopbits,
            timeout=self._params.timeout,
        )
        try:
            if not client.connect():
                raise SerialConnectionError("Unable to open serial port")

            response: Any = client.read_holding_registers(
                address=register_to_offset(start_register),
                count=count,
                device_id=self._params.slave,
            )
            if response is None:
                raise ModbusTimeoutError("No response received")
            if isinstance(response, ExceptionResponse):
                raise ModbusReadError(f"Modbus exception code {response.exception_code}")
            if getattr(response, "isError", lambda: False)():
                raise ModbusReadError(str(response))

            registers = getattr(response, "registers", None)
            if registers is None or len(registers) != count:
                raise ModbusReadError("Unexpected register payload")
            return list(registers)
        except ConnectionException as err:
            raise SerialConnectionError(str(err)) from err
        except TimeoutError as err:
            raise ModbusTimeoutError(str(err)) from err
        except ModbusTimeoutError:
            raise
        except SerialConnectionError:
            raise
        except ModbusReadError:
            raise
        except ModbusException as err:
            raise ModbusReadError(str(err)) from err
        finally:
            client.close()


def register_to_offset(register: int) -> int:
    """Convert a 4xxxx holding register to a zero-based Modbus offset."""
    return register - 40001
