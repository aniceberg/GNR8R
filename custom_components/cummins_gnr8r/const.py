from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "cummins_gnr8r"
NAME: Final = "cummins_GNR8R"
VERSION: Final = "0.1.0"

PLATFORMS: Final = ("sensor", "binary_sensor")

DEFAULT_NAME: Final = "cummins_GNR8R"
DEFAULT_MANUFACTURER: Final = "Cummins"
DEFAULT_MODEL: Final = "PowerCommand Generator"

CONF_POLL_INTERVAL: Final = "poll_interval"
CONF_SCAN_THROTTLE_MS: Final = "scan_throttle_ms"
CONF_SERIAL_PORT: Final = "serial_port"
CONF_SLAVE: Final = "slave"
CONF_BAUDRATE: Final = "baudrate"
CONF_BYTESIZE: Final = "bytesize"
CONF_PARITY: Final = "parity"
CONF_STOPBITS: Final = "stopbits"

DEFAULT_SLAVE: Final = 1
DEFAULT_BAUDRATE: Final = 9600
DEFAULT_BYTESIZE: Final = 8
DEFAULT_PARITY: Final = "N"
DEFAULT_STOPBITS: Final = 1
DEFAULT_POLL_INTERVAL: Final = 10
DEFAULT_SCAN_THROTTLE_MS: Final = 0
DEFAULT_TIMEOUT: Final = 2.0
DEFAULT_RETRIES: Final = 2

MIN_POLL_INTERVAL: Final = 5
MAX_POLL_INTERVAL: Final = 300

REGISTER_BITMAP_1: Final = 40016
REGISTER_BITMAP_2: Final = 40017
REGISTER_LINE_FREQUENCY: Final = 40044
REGISTER_BATTERY_VOLTAGE: Final = 40061
REGISTER_OIL_PRESSURE: Final = 40062
REGISTER_COOLANT_TEMPERATURE: Final = 40064
REGISTER_ENGINE_SPEED: Final = 40068
REGISTER_TOTAL_RUNS: Final = 40069

COORDINATOR_TIMEOUT: Final = timedelta(seconds=DEFAULT_TIMEOUT)

DATA_CLIENT: Final = "client"
DATA_COORDINATOR: Final = "coordinator"
