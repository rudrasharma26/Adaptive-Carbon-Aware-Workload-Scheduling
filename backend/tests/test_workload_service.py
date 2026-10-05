"""
backend/tests/test_workload_service.py

Unit tests for backend.services.workload_service.

These tests run against the REAL model and scaler — no mocks.
They verify:
  - model loads without error
  - scaler loads without error
  - load_latest_window() returns exactly LOOKBACK finite values
  - predict() returns a finite numeric value
  - prediction falls in a sensible CPU-percentage range
  - wrong history length is rejected
  - NaN in history is rejected
  - inf in history is rejected
"""

import math

import pytest

import backend.services.workload_service as svc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _real_window():
    """Return the latest 24-value window from the real CSV."""
    return svc.load_latest_window()


# ---------------------------------------------------------------------------
# Artefact loading
# ---------------------------------------------------------------------------

def test_model_loads():
    """GRU checkpoint loads and returns a GRUWorkloadPredictor instance."""
    model = svc._get_model()
    assert model is not None
    # Check the model has the expected architecture attributes
    assert hasattr(model, "gru")
    assert hasattr(model, "fc")


def test_scaler_loads():
    """MinMaxScaler loads and has the expected fitted attributes."""
    scaler = svc._get_scaler()
    assert scaler is not None
    assert hasattr(scaler, "scale_")
    assert hasattr(scaler, "data_min_")
    assert hasattr(scaler, "data_max_")
    # Sanity: scaler was fitted on CPU usage [%] in range ~8–59 %
    assert scaler.data_min_[0] < 10.0
    assert scaler.data_max_[0] > 50.0


# ---------------------------------------------------------------------------
# Window loading
# ---------------------------------------------------------------------------

def test_load_latest_window_length():
    """load_latest_window() returns exactly LOOKBACK values."""
    window = _real_window()
    assert len(window) == svc.LOOKBACK


def test_load_latest_window_all_finite():
    """All values returned by load_latest_window() are finite numbers."""
    window = _real_window()
    for v in window:
        assert math.isfinite(v), f"Non-finite value found: {v}"


def test_load_latest_window_values_are_floats():
    """load_latest_window() returns a list of plain Python floats."""
    window = _real_window()
    for v in window:
        assert isinstance(v, float)


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

def test_predict_returns_numeric():
    """predict() returns a plain Python float."""
    window = _real_window()
    result = svc.predict(window)
    assert isinstance(result, float)


def test_predict_is_finite():
    """Prediction is finite (not NaN, not inf)."""
    window = _real_window()
    result = svc.predict(window)
    assert math.isfinite(result), f"Prediction is not finite: {result}"


def test_predict_in_sensible_range():
    """Predicted CPU percentage is within a reasonable range (0 – 100 %)."""
    window = _real_window()
    result = svc.predict(window)
    # The GRU has seen data in ~8–59 %; allow generous margin for extrapolation
    assert -10.0 <= result <= 110.0, (
        f"Prediction {result:.2f} is outside the expected 0–100 % range."
    )


# ---------------------------------------------------------------------------
# Input validation — rejection cases
# ---------------------------------------------------------------------------

def test_predict_rejects_wrong_length_short():
    """predict() raises ValueError when history is too short."""
    with pytest.raises(ValueError, match="exactly 24"):
        svc.predict([50.0] * 10)


def test_predict_rejects_wrong_length_long():
    """predict() raises ValueError when history is too long."""
    with pytest.raises(ValueError, match="exactly 24"):
        svc.predict([50.0] * 30)


def test_predict_rejects_empty():
    """predict() raises ValueError for an empty list."""
    with pytest.raises(ValueError, match="exactly 24"):
        svc.predict([])


def test_predict_rejects_nan():
    """predict() raises ValueError if any history value is NaN."""
    window = _real_window()
    window[5] = float("nan")
    with pytest.raises(ValueError, match="NaN"):
        svc.predict(window)


def test_predict_rejects_positive_inf():
    """predict() raises ValueError if any history value is +inf."""
    window = _real_window()
    window[0] = float("inf")
    with pytest.raises(ValueError, match="infinite"):
        svc.predict(window)


def test_predict_rejects_negative_inf():
    """predict() raises ValueError if any history value is -inf."""
    window = _real_window()
    window[-1] = float("-inf")
    with pytest.raises(ValueError, match="infinite"):
        svc.predict(window)
