"""
backend/services/scheduler.py

Simple deterministic deadline-aware scheduler for the Carbon-Aware Workload
Scheduling prototype.

This is a FACULTY DEMO.  All energy estimates use clearly-labelled demo
constants — they are NOT physical measurements.

The scheduler is a pure function: it takes only plain Python scalars and
lists, performs arithmetic, and returns a plain dict.  No I/O, no ML, no
randomness.

Energy model (demo estimate)
----------------------------
estimated_energy_kwh =
    (BASE_POWER_KW + CPU_FACTOR * predicted_cpu_percent)
    * (workload_duration_minutes / 60.0)

CO₂ estimate
------------
estimated_co2_grams =
    estimated_energy_kwh * carbon_intensity_gco2_per_kwh

Decision logic
--------------
1.  RUN NOW immediately if no feasible delay slot exists within the deadline.
2.  Otherwise find the candidate slot with the lowest carbon intensity.
3.  DELAY only if the best candidate reduces CO₂ by more than
    CO2_SAVING_THRESHOLD_PERCENT (default 5 %).
4.  Otherwise RUN NOW.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

# ---------------------------------------------------------------------------
# Demo energy-model constants
# (labelled as estimates — not physical measurements)
# ---------------------------------------------------------------------------

#: Baseline server power draw regardless of CPU load (kW, demo estimate).
BASE_POWER_KW: float = 0.10

#: Additional power per 1 % CPU utilisation (kW per %, demo estimate).
#: Implies 0.10 kW extra at 100 % CPU → 0.20 kW total at full load.
CPU_FACTOR: float = 0.0010

#: Minimum CO₂ reduction (%) required to recommend DELAY over RUN NOW.
CO2_SAVING_THRESHOLD_PERCENT: float = 5.0


# ---------------------------------------------------------------------------
# Input / output types
# ---------------------------------------------------------------------------

@dataclass
class CarbonSlot:
    """A candidate execution slot with its associated carbon intensity."""
    timestamp: str          # ISO-8601 string (or label such as "now")
    carbon_intensity: float # gCO2eq/kWh
    delay_minutes: float    # minutes from now (0 = RUN NOW slot)


@dataclass
class SlotEstimate:
    """Energy and CO₂ estimates for a single execution slot."""
    carbon_intensity: float    # gCO2eq/kWh
    estimated_energy_kwh: float
    estimated_co2_grams: float


@dataclass
class ScheduleResult:
    """Complete scheduler output."""
    decision: str              # "RUN_NOW" or "DELAY"
    delay_minutes: float       # 0 when decision is RUN_NOW
    reason: str                # human-readable explanation
    run_now: SlotEstimate
    delayed: SlotEstimate      # best feasible delay slot (may equal run_now)
    co2_saved_grams: float     # positive = delay is greener
    savings_percent: float
    deadline_feasible: bool    # True if at least one delay slot fits deadline


# ---------------------------------------------------------------------------
# Pure helper functions
# ---------------------------------------------------------------------------

def estimate_energy_kwh(
    cpu_percent: float,
    duration_minutes: float,
) -> float:
    """
    Demo energy estimate.

    Parameters
    ----------
    cpu_percent:
        Predicted CPU utilisation percentage (0–100).
    duration_minutes:
        Workload runtime in minutes.

    Returns
    -------
    float
        Estimated energy consumption in kWh (demo model).
    """
    power_kw = BASE_POWER_KW + CPU_FACTOR * cpu_percent
    return power_kw * (duration_minutes / 60.0)


def estimate_co2_grams(
    energy_kwh: float,
    carbon_intensity_gco2_per_kwh: float,
) -> float:
    """Return estimated CO₂ in grams for given energy and carbon intensity."""
    return energy_kwh * carbon_intensity_gco2_per_kwh


def _slot_estimate(
    cpu_percent: float,
    duration_minutes: float,
    carbon_intensity: float,
) -> SlotEstimate:
    energy = estimate_energy_kwh(cpu_percent, duration_minutes)
    co2 = estimate_co2_grams(energy, carbon_intensity)
    return SlotEstimate(
        carbon_intensity=round(carbon_intensity, 4),
        estimated_energy_kwh=round(energy, 6),
        estimated_co2_grams=round(co2, 4),
    )


# ---------------------------------------------------------------------------
# Main scheduler
# ---------------------------------------------------------------------------

def schedule(
    predicted_cpu_percent: float,
    current_carbon_intensity: float,
    carbon_intensity_options: List[CarbonSlot],
    workload_duration_minutes: float,
    deadline_minutes: float,
) -> ScheduleResult:
    """
    Decide whether to run a workload now or delay it.

    Parameters
    ----------
    predicted_cpu_percent:
        GRU-predicted CPU usage for the next 5 minutes (%).
    current_carbon_intensity:
        Current grid carbon intensity (gCO2eq/kWh).
    carbon_intensity_options:
        Candidate delay slots, each with a ``delay_minutes`` offset from now
        and an associated ``carbon_intensity``.  The list may be empty.
    workload_duration_minutes:
        Estimated workload runtime (minutes).
    deadline_minutes:
        Hard deadline — the workload must START within this many minutes.

    Returns
    -------
    ScheduleResult
    """
    # Validate inputs
    if not math.isfinite(predicted_cpu_percent) or predicted_cpu_percent < 0:
        raise ValueError(
            f"predicted_cpu_percent must be a non-negative finite number, "
            f"got {predicted_cpu_percent}."
        )
    if not math.isfinite(current_carbon_intensity) or current_carbon_intensity < 0:
        raise ValueError(
            f"current_carbon_intensity must be a non-negative finite number, "
            f"got {current_carbon_intensity}."
        )
    if workload_duration_minutes <= 0:
        raise ValueError("workload_duration_minutes must be positive.")
    if deadline_minutes <= 0:
        raise ValueError("deadline_minutes must be positive.")

    # RUN NOW estimate (uses the current carbon intensity)
    run_now_est = _slot_estimate(
        predicted_cpu_percent,
        workload_duration_minutes,
        current_carbon_intensity,
    )

    # Filter candidate delay slots that fit within the deadline
    feasible_slots = [
        s for s in carbon_intensity_options
        if 0 < s.delay_minutes <= deadline_minutes
    ]
    deadline_feasible = len(feasible_slots) > 0

    # If no feasible delay slot exists → must RUN NOW
    if not deadline_feasible:
        return ScheduleResult(
            decision="RUN_NOW",
            delay_minutes=0.0,
            reason=(
                "Running now because no delay slot is available within the "
                f"{deadline_minutes:.0f}-minute deadline."
            ),
            run_now=run_now_est,
            delayed=run_now_est,   # same slot — no delay possible
            co2_saved_grams=0.0,
            savings_percent=0.0,
            deadline_feasible=False,
        )

    # Find the feasible slot with the lowest carbon intensity
    best_slot = min(feasible_slots, key=lambda s: s.carbon_intensity)
    delayed_est = _slot_estimate(
        predicted_cpu_percent,
        workload_duration_minutes,
        best_slot.carbon_intensity,
    )

    co2_saved = run_now_est.estimated_co2_grams - delayed_est.estimated_co2_grams
    savings_pct = (
        (co2_saved / run_now_est.estimated_co2_grams * 100.0)
        if run_now_est.estimated_co2_grams > 0
        else 0.0
    )

    if savings_pct >= CO2_SAVING_THRESHOLD_PERCENT:
        decision = "DELAY"
        reason = (
            f"Delay by {best_slot.delay_minutes:.0f} minutes is recommended. "
            f"The later slot has lower carbon intensity "
            f"({best_slot.carbon_intensity:.1f} vs "
            f"{current_carbon_intensity:.1f} gCO\u2082eq/kWh), "
            f"saving an estimated {co2_saved:.2f} g CO\u2082 "
            f"({savings_pct:.1f}% reduction) while remaining within the "
            f"{deadline_minutes:.0f}-minute deadline."
        )
        chosen_delay = best_slot.delay_minutes
    else:
        decision = "RUN_NOW"
        reason = (
            f"Running now is recommended. "
            f"The best available delay slot "
            f"({best_slot.carbon_intensity:.1f} gCO\u2082eq/kWh at "
            f"+{best_slot.delay_minutes:.0f} min) offers only "
            f"{savings_pct:.1f}% CO\u2082 savings — below the "
            f"{CO2_SAVING_THRESHOLD_PERCENT:.0f}% threshold for delaying."
        )
        chosen_delay = 0.0

    return ScheduleResult(
        decision=decision,
        delay_minutes=chosen_delay,
        reason=reason,
        run_now=run_now_est,
        delayed=delayed_est,
        co2_saved_grams=round(co2_saved, 4),
        savings_percent=round(savings_pct, 2),
        deadline_feasible=True,
    )
