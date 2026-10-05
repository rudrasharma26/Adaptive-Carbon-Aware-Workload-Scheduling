"""
backend/api/carbon.py

FastAPI router — carbon-intensity endpoints.

Routes
------
GET /api/carbon/current
    Most-recent carbon-intensity reading for a zone.

GET /api/carbon/history
    Short time-series of carbon-intensity observations.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.services.carbon_service import (
    CARBON_UNIT,
    DEFAULT_ZONE,
    APIRequestError,
    MissingAPIKeyError,
    get_current,
    get_history,
)

router = APIRouter(prefix="/api/carbon", tags=["carbon"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CurrentResponse(BaseModel):
    zone: str
    carbon_intensity_gco2_per_kwh: float
    timestamp: str


class HistoryPoint(BaseModel):
    timestamp: str
    carbon_intensity: float


class HistoryResponse(BaseModel):
    zone: str
    unit: str
    data: List[HistoryPoint]


# ---------------------------------------------------------------------------
# Shared error mapping
# ---------------------------------------------------------------------------

def _handle_carbon_error(exc: Exception) -> HTTPException:
    """Convert carbon-service exceptions into appropriate HTTP errors."""
    if isinstance(exc, MissingAPIKeyError):
        return HTTPException(
            status_code=503,
            detail=(
                "ELECTRICITY_MAPS_API_KEY environment variable is not set. "
                "Set it before starting the server."
            ),
        )
    if isinstance(exc, APIRequestError):
        return HTTPException(
            status_code=502,
            detail=f"Electricity Maps API error: {exc}",
        )
    # ValueError from validation
    return HTTPException(status_code=502, detail=str(exc))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/current", response_model=CurrentResponse)
def current_endpoint(
    zone: str = Query(default=DEFAULT_ZONE, description="Electricity Maps zone identifier"),
) -> CurrentResponse:
    """
    Return the most-recent carbon-intensity reading for ``zone``.
    """
    try:
        reading = get_current(zone=zone)
    except (MissingAPIKeyError, APIRequestError, ValueError) as exc:
        raise _handle_carbon_error(exc) from exc

    return CurrentResponse(
        zone=zone,
        carbon_intensity_gco2_per_kwh=reading.carbon_intensity,
        timestamp=reading.timestamp,
    )


@router.get("/history", response_model=HistoryResponse)
def history_endpoint(
    zone: str = Query(default=DEFAULT_ZONE, description="Electricity Maps zone identifier"),
    hours: int = Query(default=2, ge=1, le=24, description="Lookback window in hours"),
) -> HistoryResponse:
    """
    Return up to ``hours`` hours of recent carbon-intensity observations for
    ``zone``.  Suitable for the demo scheduler comparison.
    """
    try:
        readings = get_history(zone=zone, hours=hours)
    except (MissingAPIKeyError, APIRequestError, ValueError) as exc:
        raise _handle_carbon_error(exc) from exc

    return HistoryResponse(
        zone=zone,
        unit=CARBON_UNIT,
        data=[
            HistoryPoint(timestamp=r.timestamp, carbon_intensity=r.carbon_intensity)
            for r in readings
        ],
    )
