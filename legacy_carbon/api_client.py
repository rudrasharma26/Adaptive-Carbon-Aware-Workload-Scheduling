"""verdant/carbon/api_client.py

Utility to fetch historical carbon‑intensity data from the Electricity Maps API.
The API key is taken from the environment variable ``ELECTRICITY_MAPS_API_KEY``.

The primary public function is :func:`fetch_and_save_historical` which:

1. Validates that an API key is present.
2. Calls the Electricity Maps ``/v3/carbon-intensity/history`` endpoint
   for a single *zone* and a user‑provided ISO‑8601 ``start``/``end`` range.
3. Performs basic validation on the HTTP response and the payload:
   * non‑200 status codes raise ``RuntimeError``
   * empty payload raises ``ValueError``
   * duplicate timestamps raise ``ValueError``
   * missing ``timestamp`` or ``carbonIntensity`` fields raise ``ValueError``
   * ``None``/``NaN`` carbon values raise ``ValueError``
4. Writes the cleaned data to ``data/carbon/carbon_intensity_sample.csv``
   using the exact timestamps and units returned by the API.
   The CSV header is ``timestamp,carbon_intensity`` and the unit is documented
   in the file docstring (the API always returns grams of CO₂‑equivalent per kWh).

The module can be used directly from the command line to download a sample
period for testing purposes.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import pathlib
import sys
from typing import List, Tuple

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
API_BASE_URL = "https://api.electricitymaps.com/v3"
HISTORY_ENDPOINT = f"{API_BASE_URL}/carbon-intensity/history"

# The API always returns carbon intensity in grams of CO₂‑equivalent per kWh.
CARBON_UNIT = "gCO2eq/kWh"

# ---------------------------------------------------------------------------
# Exceptions – simple subclasses for clearer error handling.
# ---------------------------------------------------------------------------
class MissingAPIKeyError(RuntimeError):
    pass

class APIRequestError(RuntimeError):
    pass

# ---------------------------------------------------------------------------
# Core fetching logic
# ---------------------------------------------------------------------------
def _build_headers() -> dict:
    api_key = os.getenv("ELECTRICITY_MAPS_API_KEY")
    if not api_key:
        raise MissingAPIKeyError(
            "Environment variable ELECTRICITY_MAPS_API_KEY is not set"
        )
    return {"auth-token": api_key}

def _parse_iso(timestamp_str: str) -> dt.datetime:
    """Parse an ISO‑8601 timestamp returned by the API.

    The API always returns timestamps ending with a ``Z`` (UTC).  ``datetime.fromisoformat``
    does not understand the trailing ``Z`` in Python <3.11, so we replace it.
    """
    if timestamp_str.endswith("Z"):
        timestamp_str = timestamp_str[:-1] + "+00:00"
    return dt.datetime.fromisoformat(timestamp_str)

def fetch_historical(
    zone: str,
    start: str,
    end: str,
) -> List[Tuple[str, float]]:
    """Fetch historical carbon‑intensity data for *zone* between *start* and *end*.

    Parameters
    ----------
    zone: str
        Electricity‑Maps zone identifier (e.g. ``"FR"`` for France).
    start, end: str
        ISO‑8601 timestamps, e.g. ``"2026-09-30T00:00:00Z"``.

    Returns
    -------
    List[Tuple[str, float]]
        A list of ``(timestamp, carbon_intensity)`` pairs preserving the exact
        timestamp strings from the API.
    """
    params = {"zone": zone, "start": start, "end": end}
    headers = _build_headers()

    try:
        response = requests.get(HISTORY_ENDPOINT, params=params, headers=headers, timeout=15)
    except requests.RequestException as exc:
        raise APIRequestError(f"Network error while contacting Electricity Maps API: {exc}") from exc

    # Early status check before parsing JSON (important for test mocks)
    if response.status_code != 200:
        raise APIRequestError(
            f"Electricity Maps API returned status {response.status_code}: {response.text}"
        )

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        raise APIRequestError("Failed to decode JSON response from Electricity Maps API") from exc

    # Debug output – safe (no API key printed)
    print(f"HTTP status: {response.status_code}")
    if isinstance(payload, dict):
        print(f"Top-level JSON keys: {list(payload.keys())}")
        preview = json.dumps(payload)[:500]
        print(f"Response preview (truncated): {preview}")

    # Handle possible error object in a successful response
    if isinstance(payload, dict) and "error" in payload:
        raise APIRequestError(f"API error: {payload['error']}")

    # Extract data list – support v3 "data" list and possible v4 structures
    data = None
    if isinstance(payload.get("data"), list):
        data = payload["data"]
    elif isinstance(payload.get("history"), list):
        data = payload["history"]
    elif isinstance(payload.get("data"), dict) and isinstance(payload["data"].get("history"), list):
        data = payload["data"]["history"]
    if not data:
        # Preserve original error message expected by tests
        raise ValueError("API response contains no 'data' field or it is empty")

    observations: List[Tuple[str, float]] = []
    seen_timestamps = set()
    for entry in data:
        ts = entry.get("datetime", entry.get("timestamp"))
        ci = entry.get("carbonIntensity")
        if ts is None or ci is None:
            raise ValueError("Missing 'datetime'/'timestamp' or 'carbonIntensity' in an entry")
        if ts in seen_timestamps:
            raise ValueError(f"Duplicate timestamp encountered: {ts}")
        seen_timestamps.add(ts)
        try:
            ci_val = float(ci)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Carbon intensity not numeric for timestamp {ts}: {ci}") from exc
        if not (ci_val == ci_val):  # NaN check
            raise ValueError(f"Carbon intensity is NaN for timestamp {ts}")
        observations.append((ts, ci_val))

    if not observations:
        raise ValueError("No valid observations retrieved from the API")

    observations.sort(key=lambda x: x[0])
    return observations

# ---------------------------------------------------------------------------
# CSV saving helper
# ---------------------------------------------------------------------------
def save_to_csv(observations: List[Tuple[str, float]], target_path: pathlib.Path) -> None:
    """Write *observations* to ``target_path`` using the required CSV format.

    The CSV header is ``timestamp,carbon_intensity``.  The function creates the
    parent directory if it does not exist.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "carbon_intensity"])
        for ts, ci in observations:
            writer.writerow([ts, f"{ci:.3f}"])

# ---------------------------------------------------------------------------
# Public convenience function
# ---------------------------------------------------------------------------
def fetch_and_save_historical(
    zone: str,
    start: str,
    end: str,
    csv_path: pathlib.Path | None = None,
) -> List[Tuple[str, float]]:
    """Fetch data for *zone* and write it to ``csv_path``.

    If ``csv_path`` is ``None`` the default location
    ``data/carbon/carbon_intensity_sample.csv`` relative to the repository root
    is used.
    """
    observations = fetch_historical(zone, start, end)
    if csv_path is None:
        repo_root = pathlib.Path(__file__).resolve().parents[2]
        csv_path = repo_root / "data" / "carbon" / "carbon_intensity_sample.csv"
    save_to_csv(observations, csv_path)
    return observations

# ---------------------------------------------------------------------------
# Simple CLI entry point – useful for manual testing.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: python -m verdant.carbon.api_client <ZONE> <START_ISO> <END_ISO>"
        )
        sys.exit(1)
    zone_arg, start_arg, end_arg = sys.argv[1:4]
    try:
        obs = fetch_and_save_historical(zone_arg, start_arg, end_arg)
        print(f"Saved {len(obs)} observations to CSV.")
    except Exception as exc:  # pragma: no cover – CLI convenience
        print(f"Error: {exc}")
        sys.exit(1)
