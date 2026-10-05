"""
backend/tests/test_scheduler.py

Unit and integration tests for the scheduler.

Unit tests use controlled carbon values — no network, no ML model calls.
Integration tests (live API + real GRU) are auto-skipped when
ELECTRICITY_MAPS_API_KEY is not set.
"""

from __future__ import annotations

import math
import os

import pytest

from backend.services.scheduler import (
    CO2_SAVING_THRESHOLD_PERCENT,
    BASE_POWER_KW,
    CPU_FACTOR,
    CarbonSlot,
    estimate_co2_grams,
    estimate_energy_kwh,
    schedule,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slot(delay_minutes: float, ci: float, ts: str = "") -> CarbonSlot:
    return CarbonSlot(
        timestamp=ts or f"2026-10-05T10:{int(delay_minutes):02d}:00Z",
        carbon_intensity=ci,
        delay_minutes=delay_minutes,
    )


def _base_kwargs(**overrides):
    defaults = dict(
        predicted_cpu_percent=20.0,
        current_carbon_intensity=150.0,
        carbon_intensity_options=[
            _slot(10, 100.0),   # 33 % lower → well above threshold
            _slot(20, 130.0),
        ],
        workload_duration_minutes=15.0,
        deadline_minutes=30.0,
    )
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# estimate_energy_kwh
# ---------------------------------------------------------------------------

class TestEstimateEnergy:
    def test_zero_cpu_equals_base_power_only(self):
        e = estimate_energy_kwh(cpu_percent=0.0, duration_minutes=60.0)
        assert math.isclose(e, BASE_POWER_KW * 1.0, rel_tol=1e-9)

    def test_100_cpu_adds_cpu_factor(self):
        e = estimate_energy_kwh(cpu_percent=100.0, duration_minutes=60.0)
        expected = (BASE_POWER_KW + CPU_FACTOR * 100.0) * 1.0
        assert math.isclose(e, expected, rel_tol=1e-9)

    def test_half_hour_is_half_energy(self):
        e_full = estimate_energy_kwh(50.0, 60.0)
        e_half = estimate_energy_kwh(50.0, 30.0)
        assert math.isclose(e_half, e_full / 2.0, rel_tol=1e-9)

    def test_result_is_positive(self):
        assert estimate_energy_kwh(10.0, 15.0) > 0


# ---------------------------------------------------------------------------
# estimate_co2_grams
# ---------------------------------------------------------------------------

class TestEstimateCO2:
    def test_zero_energy_zero_co2(self):
        assert estimate_co2_grams(0.0, 200.0) == 0.0

    def test_zero_carbon_intensity_zero_co2(self):
        assert estimate_co2_grams(1.0, 0.0) == 0.0

    def test_multiplication_correct(self):
        assert math.isclose(estimate_co2_grams(0.05, 200.0), 10.0, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# schedule() — RUN_NOW cases
# ---------------------------------------------------------------------------

class TestScheduleRunNow:
    def test_run_now_when_no_delay_options(self):
        result = schedule(**_base_kwargs(carbon_intensity_options=[]))
        assert result.decision == "RUN_NOW"
        assert result.delay_minutes == 0.0
        assert result.deadline_feasible is False

    def test_run_now_when_all_slots_exceed_deadline(self):
        slots = [_slot(60, 50.0), _slot(90, 40.0)]  # both beyond 30-min deadline
        result = schedule(**_base_kwargs(carbon_intensity_options=slots))
        assert result.decision == "RUN_NOW"
        assert result.deadline_feasible is False

    def test_run_now_when_savings_below_threshold(self):
        # 150 → 148 gCO2/kWh = ~1.3 % savings → below 5 %
        slots = [_slot(10, 148.0)]
        result = schedule(**_base_kwargs(
            current_carbon_intensity=150.0,
            carbon_intensity_options=slots,
        ))
        assert result.decision == "RUN_NOW"
        assert result.deadline_feasible is True

    def test_run_now_when_delay_has_higher_carbon(self):
        # delay slot is worse
        slots = [_slot(10, 200.0)]
        result = schedule(**_base_kwargs(
            current_carbon_intensity=150.0,
            carbon_intensity_options=slots,
        ))
        assert result.decision == "RUN_NOW"

    def test_run_now_reason_is_non_empty(self):
        result = schedule(**_base_kwargs(carbon_intensity_options=[]))
        assert len(result.reason) > 10


# ---------------------------------------------------------------------------
# schedule() — DELAY cases
# ---------------------------------------------------------------------------

class TestScheduleDelay:
    def test_delay_when_clearly_lower_carbon(self):
        # 150 → 50 gCO2/kWh = 66 % savings
        slots = [_slot(10, 50.0)]
        result = schedule(**_base_kwargs(
            current_carbon_intensity=150.0,
            carbon_intensity_options=slots,
        ))
        assert result.decision == "DELAY"
        assert result.delay_minutes == 10.0
        assert result.deadline_feasible is True

    def test_delay_picks_lowest_carbon_slot(self):
        slots = [_slot(10, 90.0), _slot(20, 50.0), _slot(25, 70.0)]
        result = schedule(**_base_kwargs(
            current_carbon_intensity=150.0,
            carbon_intensity_options=slots,
        ))
        assert result.decision == "DELAY"
        assert result.delayed.carbon_intensity == 50.0
        assert result.delay_minutes == 20.0

    def test_delay_reason_is_non_empty(self):
        slots = [_slot(10, 50.0)]
        result = schedule(**_base_kwargs(
            current_carbon_intensity=150.0,
            carbon_intensity_options=slots,
        ))
        assert len(result.reason) > 10


# ---------------------------------------------------------------------------
# CO2 calculations
# ---------------------------------------------------------------------------

class TestCO2Calculations:
    def test_co2_saved_positive_when_delay_is_greener(self):
        slots = [_slot(10, 50.0)]
        result = schedule(**_base_kwargs(
            current_carbon_intensity=150.0,
            carbon_intensity_options=slots,
        ))
        assert result.co2_saved_grams > 0.0

    def test_co2_saved_zero_when_no_feasible_delay(self):
        result = schedule(**_base_kwargs(carbon_intensity_options=[]))
        assert result.co2_saved_grams == 0.0

    def test_savings_percent_between_0_and_100(self):
        slots = [_slot(10, 50.0)]
        result = schedule(**_base_kwargs(
            current_carbon_intensity=150.0,
            carbon_intensity_options=slots,
        ))
        assert 0.0 <= result.savings_percent <= 100.0

    def test_run_now_co2_equals_energy_times_intensity(self):
        cpu = 20.0
        duration = 15.0
        ci = 150.0
        result = schedule(**_base_kwargs(
            predicted_cpu_percent=cpu,
            current_carbon_intensity=ci,
            workload_duration_minutes=duration,
            carbon_intensity_options=[],
        ))
        expected_energy = estimate_energy_kwh(cpu, duration)
        expected_co2 = estimate_co2_grams(expected_energy, ci)
        assert math.isclose(
            result.run_now.estimated_co2_grams, round(expected_co2, 4), rel_tol=1e-6
        )


# ---------------------------------------------------------------------------
# Deadline feasibility
# ---------------------------------------------------------------------------

class TestDeadlineFeasibility:
    def test_feasible_true_when_slot_within_deadline(self):
        slots = [_slot(15, 80.0)]
        result = schedule(**_base_kwargs(
            deadline_minutes=30.0,
            carbon_intensity_options=slots,
        ))
        assert result.deadline_feasible is True

    def test_feasible_false_when_slot_beyond_deadline(self):
        slots = [_slot(45, 80.0)]   # 45 min > 30 min deadline
        result = schedule(**_base_kwargs(
            deadline_minutes=30.0,
            carbon_intensity_options=slots,
        ))
        assert result.deadline_feasible is False


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_output(self):
        kwargs = _base_kwargs()
        r1 = schedule(**kwargs)
        r2 = schedule(**kwargs)
        assert r1.decision == r2.decision
        assert r1.delay_minutes == r2.delay_minutes
        assert r1.co2_saved_grams == r2.co2_saved_grams


# ---------------------------------------------------------------------------
# Invalid inputs
# ---------------------------------------------------------------------------

class TestInvalidInputs:
    def test_negative_cpu_raises(self):
        with pytest.raises(ValueError, match="predicted_cpu_percent"):
            schedule(**_base_kwargs(predicted_cpu_percent=-1.0))

    def test_negative_carbon_raises(self):
        with pytest.raises(ValueError, match="current_carbon_intensity"):
            schedule(**_base_kwargs(current_carbon_intensity=-50.0))

    def test_zero_duration_raises(self):
        with pytest.raises(ValueError, match="workload_duration_minutes"):
            schedule(**_base_kwargs(workload_duration_minutes=0.0))

    def test_zero_deadline_raises(self):
        with pytest.raises(ValueError, match="deadline_minutes"):
            schedule(**_base_kwargs(deadline_minutes=0.0))


# ---------------------------------------------------------------------------
# Integration test — live API + real GRU (auto-skipped without key)
# ---------------------------------------------------------------------------

INTEGRATION_ENABLED = bool(os.getenv("ELECTRICITY_MAPS_API_KEY"))


@pytest.mark.skipif(
    not INTEGRATION_ENABLED,
    reason="ELECTRICITY_MAPS_API_KEY not set — skipping live pipeline test",
)
class TestIntegrationPipeline:
    def test_full_pipeline_schedule_endpoint(self):
        """End-to-end: real GRU + real carbon data → deterministic decision."""
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        resp = client.post(
            "/api/schedule",
            json={
                "workload_duration_minutes": 15,
                "deadline_minutes": 30,
                "zone": "FR",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] in ("RUN_NOW", "DELAY")
        assert isinstance(data["predicted_cpu_percent"], float)
        assert math.isfinite(data["predicted_cpu_percent"])
        assert data["current_carbon_intensity"] > 0
        assert isinstance(data["reason"], str)
        assert len(data["reason"]) > 0

    def test_demo_endpoint_complete_fields(self):
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        resp = client.get("/api/demo")
        assert resp.status_code == 200
        data = resp.json()
        required = [
            "project_name", "workload_name", "zone",
            "cpu_history", "predicted_cpu_percent",
            "current_carbon_intensity", "decision", "reason",
            "run_now", "delayed", "co2_saved_grams", "savings_percent",
        ]
        for field in required:
            assert field in data, f"Missing field: {field}"
