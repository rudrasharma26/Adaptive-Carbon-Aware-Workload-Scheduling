"""
backend/api/scheduling.py

FastAPI router — scheduling endpoints.

Routes
------
POST /api/schedule
    Full pipeline: GRU prediction → carbon history → scheduler decision.

GET  /api/demo
    Single call that populates the entire dashboard with real data.

Carbon slot strategy (no forecast API required)
------------------------------------------------
The Electricity Maps history endpoint returns measured observations from the
recent past.  For this prototype we treat those recent observations as
representative of likely near-future carbon intensity at each corresponding
time offset.  Each observation is mapped to a candidate delay slot whose
``delay_minutes`` equals how many minutes before "now" that reading occurred.
This approach uses only real measured data and is clearly labelled in the
response.  It requires no forecast endpoint and no invented values.
"""

from __future__ import annotations

import datetime as dt
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.services.carbon_service import (
    CARBON_UNIT,
    DEFAULT_ZONE,
    APIRequestError,
    CarbonReading,
    MissingAPIKeyError,
    get_history,
)
from backend.services.scheduler import (
    CO2_SAVING_THRESHOLD_PERCENT,
    CarbonSlot,
    ScheduleResult,
    schedule,
)
from backend.services.workload_service import (
    HORIZON_MINUTES,
    LOOKBACK,
    load_latest_window,
    predict,
)

router = APIRouter(tags=["scheduling"])

# ---------------------------------------------------------------------------
# Demo defaults
# ---------------------------------------------------------------------------

DEMO_ZONE: str = DEFAULT_ZONE           # "FR"
DEMO_DURATION_MINUTES: int = 15
DEMO_DEADLINE_MINUTES: int = 30
DEMO_CARBON_HISTORY_HOURS: int = 3      # wider window → more delay candidates

PROJECT_NAME: str = "Adaptive Carbon-Aware Workload Scheduling"
WORKLOAD_NAME: str = "Bitbrains VM 846"


# ---------------------------------------------------------------------------
# Helper — build carbon slots from historical readings
# ---------------------------------------------------------------------------

def _build_carbon_slots(
    readings: List[CarbonReading],
    deadline_minutes: float,
) -> tuple[CarbonReading, List[CarbonSlot]]:
    """
    Derive a current reading and a list of delay-candidate slots from a
    sorted (ascending) list of historical CarbonReading objects.

    The most recent reading is used as the "RUN NOW" carbon intensity.
    Each earlier reading is mapped to a candidate delay slot whose
    ``delay_minutes`` is how many minutes before the most recent reading it
    occurred (capped at deadline_minutes so slots outside the deadline are
    excluded from the scheduler's feasible set).

    Returns
    -------
    (current_reading, candidate_slots)
    """
    if not readings:
        raise ValueError("No carbon readings available to build slots.")

    # Most-recent reading = current intensity
    current = readings[-1]

    # Parse the most-recent timestamp so we can compute offsets
    def _parse(ts: str) -> dt.datetime:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return dt.datetime.fromisoformat(ts)

    now_ts = _parse(current.timestamp)

    slots: List[CarbonSlot] = []
    for r in readings[:-1]:       # all readings except the most recent
        try:
            then_ts = _parse(r.timestamp)
        except ValueError:
            continue
        offset_minutes = (now_ts - then_ts).total_seconds() / 60.0
        if offset_minutes <= 0:
            continue
        slots.append(
            CarbonSlot(
                timestamp=r.timestamp,
                carbon_intensity=r.carbon_intensity,
                delay_minutes=round(offset_minutes, 1),
            )
        )

    return current, slots


# ---------------------------------------------------------------------------
# Shared error handler for carbon calls
# ---------------------------------------------------------------------------

def _carbon_error(exc: Exception) -> HTTPException:
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
    return HTTPException(status_code=502, detail=str(exc))


# ---------------------------------------------------------------------------
# Shared pipeline function
# ---------------------------------------------------------------------------

def _run_pipeline(
    zone: str,
    workload_duration_minutes: float,
    deadline_minutes: float,
) -> dict:
    """
    Execute the full prototype pipeline and return a result dict.

    1. Load latest 24 CPU observations.
    2. Run GRU prediction.
    3. Fetch carbon history (3 h window for enough delay candidates).
    4. Build carbon slots.
    5. Run deterministic scheduler.
    """
    # Step 1 & 2 — workload
    cpu_history = load_latest_window()
    predicted_cpu = predict(cpu_history)

    # Step 3 — carbon data
    try:
        readings = get_history(zone=zone, hours=DEMO_CARBON_HISTORY_HOURS)
    except (MissingAPIKeyError, APIRequestError, ValueError) as exc:
        raise _carbon_error(exc) from exc

    # Step 4 — build slots
    try:
        current_reading, slots = _build_carbon_slots(readings, deadline_minutes)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Step 5 — scheduler
    result: ScheduleResult = schedule(
        predicted_cpu_percent=predicted_cpu,
        current_carbon_intensity=current_reading.carbon_intensity,
        carbon_intensity_options=slots,
        workload_duration_minutes=workload_duration_minutes,
        deadline_minutes=deadline_minutes,
    )

    return {
        "cpu_history": cpu_history,
        "predicted_cpu_percent": round(predicted_cpu, 4),
        "current_reading": current_reading,
        "all_readings": readings,
        "slots": slots,
        "result": result,
        "zone": zone,
        "workload_duration_minutes": workload_duration_minutes,
        "deadline_minutes": deadline_minutes,
    }


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class ScheduleRequest(BaseModel):
    workload_duration_minutes: float = Field(
        default=15.0, gt=0, le=480,
        description="Estimated workload runtime in minutes.",
    )
    deadline_minutes: float = Field(
        default=30.0, gt=0, le=1440,
        description="Hard deadline: workload must start within this many minutes.",
    )
    zone: str = Field(
        default=DEFAULT_ZONE,
        description="Electricity Maps zone identifier (e.g. 'FR', 'DE').",
    )


class SlotEstimateOut(BaseModel):
    carbon_intensity: float
    estimated_energy_kwh: float
    estimated_co2_grams: float


class ScheduleResponse(BaseModel):
    zone: str
    predicted_cpu_percent: float
    current_carbon_intensity: float
    current_carbon_timestamp: str
    carbon_data_used: List[dict]
    workload_duration_minutes: float
    deadline_minutes: float
    decision: str
    delay_minutes: float
    reason: str
    run_now: SlotEstimateOut
    delayed: SlotEstimateOut
    co2_saved_grams: float
    savings_percent: float
    deadline_feasible: bool


class DemoResponse(BaseModel):
    project_name: str
    workload_name: str
    zone: str
    # Workload
    cpu_history: List[float]
    lookback: int
    horizon_minutes: int
    predicted_cpu_percent: float
    # Carbon
    current_carbon_intensity: float
    current_carbon_timestamp: str
    carbon_unit: str
    carbon_time_series: List[dict]
    carbon_data_note: str
    # Workload config
    workload_duration_minutes: float
    deadline_minutes: float
    # Decision
    decision: str
    delay_minutes: float
    reason: str
    run_now: SlotEstimateOut
    delayed: SlotEstimateOut
    co2_saved_grams: float
    savings_percent: float
    deadline_feasible: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/api/schedule", response_model=ScheduleResponse, tags=["scheduling"])
def schedule_endpoint(body: ScheduleRequest) -> ScheduleResponse:
    """
    Run the full carbon-aware scheduling pipeline.

    Loads real CPU history from VM 846, runs the GRU, fetches real Electricity
    Maps carbon data, then returns the deterministic scheduler decision.
    """
    p = _run_pipeline(
        zone=body.zone,
        workload_duration_minutes=body.workload_duration_minutes,
        deadline_minutes=body.deadline_minutes,
    )
    r = p["result"]
    current = p["current_reading"]

    return ScheduleResponse(
        zone=p["zone"],
        predicted_cpu_percent=p["predicted_cpu_percent"],
        current_carbon_intensity=current.carbon_intensity,
        current_carbon_timestamp=current.timestamp,
        carbon_data_used=[
            {"timestamp": rd.timestamp, "carbon_intensity": rd.carbon_intensity}
            for rd in p["all_readings"]
        ],
        workload_duration_minutes=p["workload_duration_minutes"],
        deadline_minutes=p["deadline_minutes"],
        decision=r.decision,
        delay_minutes=r.delay_minutes,
        reason=r.reason,
        run_now=SlotEstimateOut(
            carbon_intensity=r.run_now.carbon_intensity,
            estimated_energy_kwh=r.run_now.estimated_energy_kwh,
            estimated_co2_grams=r.run_now.estimated_co2_grams,
        ),
        delayed=SlotEstimateOut(
            carbon_intensity=r.delayed.carbon_intensity,
            estimated_energy_kwh=r.delayed.estimated_energy_kwh,
            estimated_co2_grams=r.delayed.estimated_co2_grams,
        ),
        co2_saved_grams=r.co2_saved_grams,
        savings_percent=r.savings_percent,
        deadline_feasible=r.deadline_feasible,
    )


@router.get("/api/demo", response_model=DemoResponse, tags=["scheduling"])
def demo_endpoint() -> DemoResponse:
    """
    Single endpoint for the dashboard.

    Returns the complete scheduling decision using demo defaults:
    zone=FR, duration=15 min, deadline=30 min.
    """
    p = _run_pipeline(
        zone=DEMO_ZONE,
        workload_duration_minutes=DEMO_DURATION_MINUTES,
        deadline_minutes=DEMO_DEADLINE_MINUTES,
    )
    r = p["result"]
    current = p["current_reading"]
    cpu_history = p["cpu_history"]

    return DemoResponse(
        project_name=PROJECT_NAME,
        workload_name=WORKLOAD_NAME,
        zone=p["zone"],
        cpu_history=[round(v, 4) for v in cpu_history],
        lookback=LOOKBACK,
        horizon_minutes=HORIZON_MINUTES,
        predicted_cpu_percent=p["predicted_cpu_percent"],
        current_carbon_intensity=current.carbon_intensity,
        current_carbon_timestamp=current.timestamp,
        carbon_unit=CARBON_UNIT,
        carbon_time_series=[
            {"timestamp": rd.timestamp, "carbon_intensity": rd.carbon_intensity}
            for rd in p["all_readings"]
        ],
        carbon_data_note=(
            "Carbon data sourced from Electricity Maps historical API. "
            "Earlier readings are used as representative delay-slot candidates "
            "within the deadline window."
        ),
        workload_duration_minutes=p["workload_duration_minutes"],
        deadline_minutes=p["deadline_minutes"],
        decision=r.decision,
        delay_minutes=r.delay_minutes,
        reason=r.reason,
        run_now=SlotEstimateOut(
            carbon_intensity=r.run_now.carbon_intensity,
            estimated_energy_kwh=r.run_now.estimated_energy_kwh,
            estimated_co2_grams=r.run_now.estimated_co2_grams,
        ),
        delayed=SlotEstimateOut(
            carbon_intensity=r.delayed.carbon_intensity,
            estimated_energy_kwh=r.delayed.estimated_energy_kwh,
            estimated_co2_grams=r.delayed.estimated_co2_grams,
        ),
        co2_saved_grams=r.co2_saved_grams,
        savings_percent=r.savings_percent,
        deadline_feasible=r.deadline_feasible,
    )
