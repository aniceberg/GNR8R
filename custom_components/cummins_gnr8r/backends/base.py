from __future__ import annotations

from typing import Protocol

from ..models import BackendUpdate


class CumminsBackendError(Exception):
    """Base backend error."""


class DiscreteEntityValidationError(CumminsBackendError):
    """Raised when a mapped Home Assistant entity is invalid."""


class CumminsBackend(Protocol):
    """Protocol implemented by all generator backends."""

    backend_type: str
    backend_name: str
    device_model: str
    source_identifier: str

    async def async_fetch(self) -> BackendUpdate:
        """Fetch the latest backend data."""
