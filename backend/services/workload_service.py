"""
backend/services/workload_service.py

Workload forecasting service.

Loads the existing trained GRU model (models/saved/gru_model.pt) and the
fitted MinMaxScaler (data/processed/scaler.pkl) once at module import time,
then exposes a predict() function for single-step CPU-usage forecasting.

Nothing here retrains the model.  The original artefacts are read-only.
"""

from __future__ import annotations

import math
import pathlib
import pickle
import sys
from typing import List, Sequence

import numpy as np
import pandas as pd
import torch

# ---------------------------------------------------------------------------
# Path setup — make legacy_model importable without installing it
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_LEGACY_MODEL_DIR = _REPO_ROOT / "legacy_model"
if str(_LEGACY_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGACY_MODEL_DIR))

from gru_model import GRUWorkloadPredictor  # noqa: E402  (legacy import)

# ---------------------------------------------------------------------------
# Artefact paths
# ---------------------------------------------------------------------------
_MODEL_PATH = _REPO_ROOT / "models" / "saved" / "gru_model.pt"
_SCALER_PATH = _REPO_ROOT / "data" / "processed" / "scaler.pkl"
_WORKLOAD_CSV = _REPO_ROOT / "data" / "workload" / "846.csv"

# ---------------------------------------------------------------------------
# Fixed hyper-parameters that match the saved checkpoint
# ---------------------------------------------------------------------------
LOOKBACK: int = 24        # number of historical observations required
HORIZON_MINUTES: int = 5  # each step ≈ 5 minutes → prediction horizon

_GRU_INPUT_DIM: int = 1
_GRU_HIDDEN_DIM: int = 64
_GRU_NUM_LAYERS: int = 1
_GRU_DROPOUT: float = 0.2

# ---------------------------------------------------------------------------
# Module-level singletons (loaded once)
# ---------------------------------------------------------------------------

def _load_model() -> GRUWorkloadPredictor:
    """Instantiate GRUWorkloadPredictor and load the saved state dict."""
    model = GRUWorkloadPredictor(
        input_dim=_GRU_INPUT_DIM,
        hidden_dim=_GRU_HIDDEN_DIM,
        num_layers=_GRU_NUM_LAYERS,
        dropout=_GRU_DROPOUT,
    )
    state_dict = torch.load(_MODEL_PATH, map_location="cpu", weights_only=False)
    model.load_state_dict(state_dict)
    model.eval()
    return model


def _load_scaler():
    """Load the fitted sklearn MinMaxScaler."""
    with open(_SCALER_PATH, "rb") as fh:
        return pickle.load(fh)


# Singletons — resolved at first access via module-level variables
_model: GRUWorkloadPredictor | None = None
_scaler = None


def _get_model() -> GRUWorkloadPredictor:
    global _model
    if _model is None:
        _model = _load_model()
    return _model


def _get_scaler():
    global _scaler
    if _scaler is None:
        _scaler = _load_scaler()
    return _scaler


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_history(cpu_history: Sequence[float]) -> np.ndarray:
    """
    Validate a sequence of CPU-usage values intended as model input.

    Raises
    ------
    ValueError
        If length ≠ LOOKBACK, or any value is NaN / infinite.
    """
    if len(cpu_history) != LOOKBACK:
        raise ValueError(
            f"cpu_history must contain exactly {LOOKBACK} values, "
            f"got {len(cpu_history)}."
        )

    arr = np.array(cpu_history, dtype=np.float64)

    if np.any(np.isnan(arr)):
        raise ValueError("cpu_history contains one or more NaN values.")
    if np.any(np.isinf(arr)):
        raise ValueError("cpu_history contains one or more infinite values.")

    return arr


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict(cpu_history: Sequence[float]) -> float:
    """
    Predict the next-5-minute CPU usage percentage.

    Parameters
    ----------
    cpu_history : sequence of float
        Exactly LOOKBACK (24) raw CPU-usage-percentage values in
        chronological order (oldest first).

    Returns
    -------
    float
        Predicted CPU usage percentage (inverse-transformed, same scale as
        the original ``CPU usage [%]`` column in the workload CSV).

    Raises
    ------
    ValueError
        On invalid input (wrong length, NaN, or infinite values).
    """
    arr = _validate_history(cpu_history)

    scaler = _get_scaler()
    model = _get_model()

    # Scale: scaler expects shape (n_samples, n_features)
    scaled = scaler.transform(arr.reshape(-1, 1)).flatten()  # shape: (24,)

    # Build model input tensor: (1, lookback, 1)
    x = torch.tensor(scaled, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
    # x.shape == (1, 24, 1)

    with torch.inference_mode():
        scaled_pred = model(x).item()  # scalar, in [0, 1] range approximately

    # Inverse-transform back to CPU percentage
    predicted_cpu: float = scaler.inverse_transform([[scaled_pred]])[0][0]
    return float(predicted_cpu)


def load_latest_window() -> List[float]:
    """
    Read the workload CSV and return the latest LOOKBACK CPU observations.

    The CSV uses semicolon as the delimiter.  Column names are stripped of
    leading/trailing whitespace.

    Returns
    -------
    List[float]
        The most recent LOOKBACK (24) values from the ``CPU usage [%]``
        column, in chronological order (oldest first).

    Raises
    ------
    ValueError
        If the CSV has fewer than LOOKBACK rows.
    """
    df = pd.read_csv(_WORKLOAD_CSV, sep=";")
    df.columns = [c.strip() for c in df.columns]

    col = "CPU usage [%]"
    if col not in df.columns:
        raise ValueError(
            f"Column '{col}' not found in workload CSV. "
            f"Available columns: {df.columns.tolist()}"
        )

    series = df[col].dropna()
    if len(series) < LOOKBACK:
        raise ValueError(
            f"Workload CSV has only {len(series)} valid rows; "
            f"need at least {LOOKBACK}."
        )

    window = series.iloc[-LOOKBACK:].tolist()
    return [float(v) for v in window]
