"""
backend/services/carbon_service.py

Carbon-intensity service for the Adaptive Carbon-Aware Workload Scheduling prototype.

Wraps the verified Electricity Maps client (legacy_carbon/api_client.py).

Public functions
----------------
get_current(zone)
    Fetch the most-recent carbon-intensity reading for a zone.
    Returns a CarbonReading dataclass.

get_history(zone, hours)
    Fetch up to ``hours`` hours of recent carbon-intensity observations.
    Returns a list of CarbonReading dataclasses.

The API key must be present in the environment variable
``ELECTRICITY_MAPS_API_KEY``.  This module never touches the key directly;
the legacy client handles auth and raises ``MissingAPIKeyError`` when the
variable is absent.
"""

from __future__ import annotations

import datetime as dt
import math
import pathlib
import sys
from dataclasses import dataclass
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Make legacy_carbon importable from the repo root
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_LEGACY_CARBON_DIR = _REPO_ROOT / "legacy_carbon"
if str(_LEGACY_CARBON_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGACY_CARBON_DIR))

# Re-export the legacy exceptions so callers only need to import from here.
from api_client import (  # noqa: E402
    APIRequestError,
    MissingAPIKeyError,
    fetch_historical,
)

# ---------------------------------------------------------------------------
# Carbon unit (mirrors the constant in the legacy client)
# ---------------------------------------------------------------------------
CARBON_UNIT: str = "gCO2eq/kWh"
DEFAULT_ZONE: str = "FR"

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CarbonReading:
    """A single carbon-intensity observation."""
    timestamp: str          # ISO-8601 string exactly as returned by the API
    carbon_intensity: float # gCO2eq/kWh


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _iso(ts: dt.datetime) -> str:
    """Format a datetime as an ISO-8601 string with Z suffix."""
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_observations(
    observations: List[Tuple[str, float]],
) -> List[CarbonReading]:
    """
    Convert raw (timestamp, value) tuples from the legacy client into
    CarbonReading objects, applying basic sanity checks.

    Raises
    ------
    ValueError
        If any carbon-intensity value is non-finite.
    """
    readings: List[CarbonReading] = []
    for ts, ci in observations:
        if not math.isfinite(ci):
            raise ValueError(
                f"Non-finite carbon intensity ({ci}) at timestamp {ts}."
            )
        readings.append(CarbonReading(timestamp=ts, carbon_intensity=ci))
    return readings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_history(
    zone: str = DEFAULT_ZONE,
    hours: int = 2,
) -> List[CarbonReading]:
    """
    Return up to ``hours`` hours of recent carbon-intensity observations for
    ``zone``.

    The Electricity Maps history endpoint returns up to 24 hours of data per
    call.  We request a window of ``hours`` hours ending at the current UTC
    time.

    Parameters
    ----------
    zone : str
        Electricity Maps zone identifier (e.g. ``"FR"`` or ``"DE"``).
    hours : int
        Width of the lookback window in hours (capped at 24).

    Returns
    -------
    List[CarbonReading]
        Observations in ascending timestamp order.

    Raises
    ------
    MissingAPIKeyError
        When ``ELECTRICITY_MAPS_API_KEY`` is not set.
    APIRequestError
        When the HTTP request fails or the API returns a non-200 status.
    ValueError
        When the response payload is empty or contains invalid values.
    """
    hours = max(1, min(hours, 24))  # clamp to a safe range

    end = _now_utc()
    start = end - dt.timedelta(hours=hours)

    observations = fetch_historical(zone, _iso(start), _iso(end))
    return _validate_observations(observations)


def get_current(zone: str = DEFAULT_ZONE) -> CarbonReading:
    """
    Return the most-recent carbon-intensity reading for ``zone``.

    Internally fetches the last hour of history and returns the observation
    with the latest timestamp.

    Raises
    ------
    MissingAPIKeyError
        When ``ELECTRICITY_MAPS_API_KEY`` is not set.
    APIRequestError
        When the HTTP request fails.
    ValueError
        When the API returns no valid observations.
    """
    readings = get_history(zone=zone, hours=1)
    if not readings:
        raise ValueError(f"No carbon-intensity data available for zone '{zone}'.")
    # readings are sorted by the legacy client; take the last one
    return readings[-1]
