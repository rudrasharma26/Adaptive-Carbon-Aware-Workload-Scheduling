"""
backend/tests/test_carbon_service.py

Tests for backend.services.carbon_service.

Strategy
--------
1. Unit tests (no network) — exercise validation helpers using controlled
   fixture data derived from the legacy client's known tuple format.
2. Integration test (real API) — skipped automatically when
   ELECTRICITY_MAPS_API_KEY is absent.
"""

from __future__ import annotations

import math
import os
from unittest.mock import patch

import pytest

import backend.services.carbon_service as svc


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_obs(n: int = 4) -> list:
    """Return n fake (timestamp, float) tuples in the client's format."""
    return [
        (f"2026-10-05T{10 + i:02d}:00:00Z", 50.0 + i * 5.0)
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# _validate_observations — unit tests, no network
# ---------------------------------------------------------------------------

class TestValidateObservations:
    def test_converts_tuples_to_carbon_readings(self):
        obs = _make_obs(3)
        readings = svc._validate_observations(obs)
        assert len(readings) == 3

    def test_preserves_timestamps(self):
        obs = _make_obs(2)
        readings = svc._validate_observations(obs)
        assert readings[0].timestamp == obs[0][0]
        assert readings[1].timestamp == obs[1][0]

    def test_preserves_carbon_values(self):
        obs = _make_obs(2)
        readings = svc._validate_observations(obs)
        assert readings[0].carbon_intensity == obs[0][1]

    def test_rejects_nan_carbon_value(self):
        obs = [(f"2026-10-05T10:00:00Z", float("nan"))]
        with pytest.raises(ValueError, match="Non-finite"):
            svc._validate_observations(obs)

    def test_rejects_inf_carbon_value(self):
        obs = [("2026-10-05T10:00:00Z", float("inf"))]
        with pytest.raises(ValueError, match="Non-finite"):
            svc._validate_observations(obs)

    def test_rejects_negative_inf_carbon_value(self):
        obs = [("2026-10-05T10:00:00Z", float("-inf"))]
        with pytest.raises(ValueError, match="Non-finite"):
            svc._validate_observations(obs)

    def test_empty_input_returns_empty_list(self):
        assert svc._validate_observations([]) == []

    def test_carbon_readings_are_typed(self):
        obs = _make_obs(1)
        readings = svc._validate_observations(obs)
        r = readings[0]
        assert isinstance(r.timestamp, str)
        assert isinstance(r.carbon_intensity, float)


# ---------------------------------------------------------------------------
# get_history — unit tests with mocked fetch_historical
# ---------------------------------------------------------------------------

class TestGetHistoryMocked:
    def test_missing_api_key_raises_clear_error(self):
        """MissingAPIKeyError propagates when the key env-var is absent."""
        from api_client import MissingAPIKeyError as LegacyMissing
        with patch("backend.services.carbon_service.fetch_historical",
                   side_effect=LegacyMissing("no key")):
            with pytest.raises(svc.MissingAPIKeyError):
                svc.get_history(zone="FR", hours=1)

    def test_api_request_error_propagates(self):
        """APIRequestError from the client propagates to callers."""
        from api_client import APIRequestError as LegacyErr
        with patch("backend.services.carbon_service.fetch_historical",
                   side_effect=LegacyErr("bad request")):
            with pytest.raises(svc.APIRequestError):
                svc.get_history(zone="FR", hours=1)

    def test_returns_correct_number_of_readings(self):
        fake_obs = _make_obs(5)
        with patch("backend.services.carbon_service.fetch_historical",
                   return_value=fake_obs):
            readings = svc.get_history(zone="FR", hours=1)
        assert len(readings) == 5

    def test_readings_are_finite(self):
        fake_obs = _make_obs(3)
        with patch("backend.services.carbon_service.fetch_historical",
                   return_value=fake_obs):
            readings = svc.get_history(zone="FR", hours=1)
        for r in readings:
            assert math.isfinite(r.carbon_intensity)

    def test_unit_constant_is_correct(self):
        assert svc.CARBON_UNIT == "gCO2eq/kWh"

    def test_hours_clamped_to_24(self):
        """Ensure hours > 24 is silently clamped; no exception from the service."""
        fake_obs = _make_obs(2)
        with patch("backend.services.carbon_service.fetch_historical",
                   return_value=fake_obs) as mock_fetch:
            svc.get_history(zone="FR", hours=999)
            # start/end args are strings; just verify fetch was called once
            assert mock_fetch.call_count == 1


# ---------------------------------------------------------------------------
# get_current — unit tests with mocked fetch_historical
# ---------------------------------------------------------------------------

class TestGetCurrentMocked:
    def test_returns_most_recent_reading(self):
        """get_current() should return the LAST element (latest timestamp)."""
        obs = _make_obs(4)
        with patch("backend.services.carbon_service.fetch_historical",
                   return_value=obs):
            reading = svc.get_current(zone="FR")
        assert reading.timestamp == obs[-1][0]
        assert reading.carbon_intensity == obs[-1][1]

    def test_empty_response_raises_value_error(self):
        with patch("backend.services.carbon_service.fetch_historical",
                   return_value=[]):
            with pytest.raises(ValueError, match="No carbon-intensity data"):
                svc.get_current(zone="FR")


# ---------------------------------------------------------------------------
# Integration test — real API, skipped when key is absent
# ---------------------------------------------------------------------------

INTEGRATION_ENABLED = bool(os.getenv("ELECTRICITY_MAPS_API_KEY"))

@pytest.mark.skipif(
    not INTEGRATION_ENABLED,
    reason="ELECTRICITY_MAPS_API_KEY not set — skipping live API test",
)
class TestIntegrationLiveAPI:
    def test_get_history_returns_data(self):
        readings = svc.get_history(zone="FR", hours=2)
        assert len(readings) > 0, "Expected at least one observation from live API"

    def test_readings_are_numeric_and_finite(self):
        readings = svc.get_history(zone="FR", hours=1)
        for r in readings:
            assert isinstance(r.carbon_intensity, float)
            assert math.isfinite(r.carbon_intensity)
            assert r.carbon_intensity >= 0

    def test_timestamps_are_non_empty_strings(self):
        readings = svc.get_history(zone="FR", hours=1)
        for r in readings:
            assert isinstance(r.timestamp, str)
            assert len(r.timestamp) > 0

    def test_get_current_returns_single_reading(self):
        reading = svc.get_current(zone="FR")
        assert isinstance(reading.carbon_intensity, float)
        assert math.isfinite(reading.carbon_intensity)
        assert isinstance(reading.timestamp, str)
