from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .backends.base import CumminsBackend, CumminsBackendError
from .const import (
    DEFAULT_MANUFACTURER,
    DERIVED_RUNNING_ON_GENERATOR,
    DERIVED_TRANSFER_IN_PROGRESS,
    DERIVED_UTILITY_OUTAGE_ACTIVE,
    DOMAIN,
    ROLE_ATS_ON_GENERATOR,
    ROLE_GENERATOR_FAULT,
    ROLE_UTILITY_AVAILABLE,
    STATE_TEXT_KEY,
)
from .models import CoordinatorSnapshot
from .status import decode_operating_status

_LOGGER = logging.getLogger(__name__)


class CumminsGeneratorCoordinator(DataUpdateCoordinator[CoordinatorSnapshot]):
    """Coordinate Modbus polling for a single generator."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        backend: CumminsBackend,
        poll_interval_seconds: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval_seconds),
        )
        self.entry = entry
        self.backend = backend
        self.domain = DOMAIN
        self.device_identifier = entry.entry_id
        self.device_name = entry.title or "cummins_GNR8R"
        self.device_model = backend.device_model
        self.manufacturer = DEFAULT_MANUFACTURER
        self.last_exception_type: str | None = None
        self.last_exception_message: str | None = None

    async def _async_update_data(self) -> CoordinatorSnapshot:
        """Poll the active backend and synthesize logical state."""
        try:
            backend_update = await self.backend.async_fetch()
        except CumminsBackendError as err:
            self.last_exception_type = type(err).__name__
            self.last_exception_message = str(err)
            raise UpdateFailed(str(err)) from err

        self.last_exception_type = None
        self.last_exception_message = None
        values: dict[str, object] = dict(backend_update.values)
        values.update(backend_update.logical_signals)
        values.update(decode_operating_status(values))
        values.update(_synthesize_values(backend_update.logical_signals))

        return CoordinatorSnapshot(
            backend=backend_update.backend,
            values=values,
            details=backend_update.details,
            fetched_at=dt_util.utcnow(),
        )


def _synthesize_values(logical_signals: dict[str, bool | None]) -> dict[str, bool | str | None]:
    """Synthesize derived entities from logical signal values."""
    utility_available = logical_signals.get(ROLE_UTILITY_AVAILABLE)
    ats_on_generator = logical_signals.get(ROLE_ATS_ON_GENERATOR)
    generator_fault = logical_signals.get(ROLE_GENERATOR_FAULT)

    running_on_generator = (
        (not utility_available) and ats_on_generator
        if utility_available is not None and ats_on_generator is not None
        else None
    )
    utility_outage_active = not utility_available if utility_available is not None else None
    transfer_in_progress = (
        utility_available == ats_on_generator
        if utility_available is not None and ats_on_generator is not None
        else None
    )

    if utility_available is None or ats_on_generator is None:
        state_text = "Transition / unknown"
    elif not utility_available and not ats_on_generator:
        state_text = "Outage detected, waiting for transfer"
    elif not utility_available and ats_on_generator:
        state_text = "Running on generator"
    elif utility_available and ats_on_generator:
        state_text = "Utility restored, awaiting retransfer"
    else:
        state_text = "Normal utility power"

    if generator_fault:
        state_text = f"{state_text} - Fault active"

    return {
        DERIVED_RUNNING_ON_GENERATOR: running_on_generator,
        DERIVED_UTILITY_OUTAGE_ACTIVE: utility_outage_active,
        DERIVED_TRANSFER_IN_PROGRESS: transfer_in_progress,
        STATE_TEXT_KEY: state_text,
    }
