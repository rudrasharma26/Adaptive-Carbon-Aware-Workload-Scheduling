"""
backend/api/workload.py

FastAPI router — workload forecasting endpoints.

Routes
------
POST /api/workload/predict
    Accept a 24-value CPU history and return the GRU prediction.

GET  /api/workload/demo
    Load the latest 24 real CPU observations from 846.csv and return both the
    window and the prediction.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from backend.services.workload_service import (
    HORIZON_MINUTES,
    LOOKBACK,
    load_latest_window,
    predict,
)

router = APIRouter(prefix="/api/workload", tags=["workload"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    cpu_history: List[float]

    @field_validator("cpu_history")
    @classmethod
    def must_have_lookback_values(cls, v: List[float]) -> List[float]:
        if len(v) != LOOKBACK:
            raise ValueError(
                f"cpu_history must contain exactly {LOOKBACK} values, got {len(v)}."
            )
        return v


class PredictResponse(BaseModel):
    predicted_cpu_percent: float
    lookback: int
    horizon_minutes: int


class DemoResponse(BaseModel):
    cpu_history: List[float]
    predicted_cpu_percent: float
    lookback: int
    horizon_minutes: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/predict", response_model=PredictResponse)
def predict_endpoint(body: PredictRequest) -> PredictResponse:
    """
    Run the GRU model on a caller-supplied 24-value CPU history.

    Returns the predicted CPU usage percentage for the next 5 minutes.
    """
    try:
        predicted = predict(body.cpu_history)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return PredictResponse(
        predicted_cpu_percent=round(predicted, 4),
        lookback=LOOKBACK,
        horizon_minutes=HORIZON_MINUTES,
    )


@router.get("/demo", response_model=DemoResponse)
def demo_endpoint() -> DemoResponse:
    """
    Load the latest 24 CPU observations from the real Bitbrains 846 trace,
    run the GRU, and return both the window and the prediction.
    """
    try:
        window = load_latest_window()
        predicted = predict(window)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return DemoResponse(
        cpu_history=[round(v, 4) for v in window],
        predicted_cpu_percent=round(predicted, 4),
        lookback=LOOKBACK,
        horizon_minutes=HORIZON_MINUTES,
    )
