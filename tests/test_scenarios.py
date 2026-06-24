"""Tests for scenarios.py — what-if scenario modifiers."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from scenarios import apply_scenario, run_scenario, run_named_scenario, ScenarioResult
from stress_engine import build_snapshot, WaterSnapshot
from config import SCENARIO_DEFAULTS


def _make_snap(
    region="CAL",
    streamflow_pctile=18.0,
    reservoir_pct=55.0,
    d0=80.0, d1=60.0, d2=40.0, d3=15.0, d4=2.0,
) -> WaterSnapshot:
    return build_snapshot(
        region=region, date="2026-06-24",
        streamflow_pctile=streamflow_pctile,
        drought_d0_pct=d0, drought_d1_pct=d1,
        drought_d2_pct=d2, drought_d3_pct=d3, drought_d4_pct=d4,
        reservoir_pct=reservoir_pct,
    )


def _make_low_snap() -> WaterSnapshot:
    return build_snapshot(
        region="GPLN", date="2026-06-24",
        streamflow_pctile=68.0,
        drought_d0_pct=12.0, drought_d1_pct=5.0,
        drought_d2_pct=1.0, drought_d3_pct=0.0, drought_d4_pct=0.0,
        reservoir_pct=78.0,
    )


# ---------------------------------------------------------------------------
# apply_scenario
# ---------------------------------------------------------------------------

class TestApplyScenario:
    def test_no_changes_returns_same_score(self):
        snap = _make_snap()
        modified = apply_scenario(snap)
        assert modified.stress_score == pytest.approx(snap.stress_score)

    def test_streamflow_delta_negative_increases_stress(self):
        snap = _make_snap()
        modified = apply_scenario(snap, streamflow_pctile_delta=-20.0)
        assert modified.stress_score > snap.stress_score

    def test_streamflow_delta_positive_decreases_stress(self):
        snap = _make_snap()
        modified = apply_scenario(snap, streamflow_pctile_delta=+20.0)
        assert modified.stress_score < snap.stress_score

    def test_drought_delta_positive_increases_stress(self):
        snap = _make_snap()
        modified = apply_scenario(snap, drought_index_delta=+25.0)
        assert modified.stress_score > snap.stress_score

    def test_drought_delta_negative_decreases_stress(self):
        snap = _make_snap()
        modified = apply_scenario(snap, drought_index_delta=-20.0)
        assert modified.stress_score < snap.stress_score

    def test_reservoir_override_to_low_increases_stress(self):
        snap = _make_snap(reservoir_pct=80.0)
        modified = apply_scenario(snap, reservoir_pct_override=10.0)
        assert modified.stress_score > snap.stress_score

    def test_reservoir_override_applied(self):
        snap = _make_snap(reservoir_pct=80.0)
        modified = apply_scenario(snap, reservoir_pct_override=20.0)
        assert modified.reservoir_pct == pytest.approx(20.0)

    def test_streamflow_pctile_clamped_at_zero(self):
        snap = _make_snap(streamflow_pctile=5.0)
        modified = apply_scenario(snap, streamflow_pctile_delta=-50.0)
        assert modified.streamflow_pctile >= 0.0

    def test_streamflow_pctile_clamped_at_100(self):
        snap = _make_snap(streamflow_pctile=90.0)
        modified = apply_scenario(snap, streamflow_pctile_delta=+50.0)
        assert modified.streamflow_pctile <= 100.0

    def test_drought_index_clamped_at_zero(self):
        snap = _make_snap(d0=5.0, d1=0.0, d2=0.0, d3=0.0, d4=0.0)
        modified = apply_scenario(snap, drought_index_delta=-100.0)
        assert modified.drought_index >= 0.0

    def test_drought_index_clamped_at_100(self):
        snap = _make_snap()
        modified = apply_scenario(snap, drought_index_delta=+200.0)
        assert modified.drought_index <= 100.0

    def test_modified_score_in_range(self):
        snap = _make_snap()
        modified = apply_scenario(snap, streamflow_pctile_delta=-40.0, drought_index_delta=+25.0)
        assert 0.0 <= modified.stress_score <= 100.0

    def test_tier_recalculated(self):
        snap = _make_snap()
        modified = apply_scenario(snap, streamflow_pctile_delta=-50.0, drought_index_delta=+40.0)
        # Should push to CRITICAL or HIGH
        assert modified.tier in {"HIGH", "CRITICAL"}

    def test_none_reservoir_override_preserves_none(self):
        snap = build_snapshot(
            region="SWUS", date="2026-06-24",
            streamflow_pctile=3.0,
            drought_d0_pct=99.0, drought_d1_pct=95.0,
            drought_d2_pct=85.0, drought_d3_pct=60.0, drought_d4_pct=25.0,
        )
        modified = apply_scenario(snap)  # reservoir_pct_override=None
        assert modified.reservoir_pct is None

    def test_supply_stress_recalculated(self):
        snap = _make_snap(streamflow_pctile=50.0, reservoir_pct=None)
        modified = apply_scenario(snap, streamflow_pctile_delta=-30.0)
        assert modified.supply_stress != snap.supply_stress


# ---------------------------------------------------------------------------
# run_scenario
# ---------------------------------------------------------------------------

class TestRunScenario:
    def test_returns_scenario_result(self):
        snap = _make_snap()
        result = run_scenario(snap, "test", streamflow_pctile_delta=-20.0)
        assert isinstance(result, ScenarioResult)

    def test_scenario_name_set(self):
        snap = _make_snap()
        result = run_scenario(snap, "my_scenario")
        assert result.scenario == "my_scenario"

    def test_base_is_original(self):
        snap = _make_snap()
        result = run_scenario(snap, "test")
        assert result.base is snap

    def test_delta_score_computed(self):
        snap = _make_snap()
        result = run_scenario(snap, "test", drought_index_delta=+20.0)
        assert result.delta_score == pytest.approx(
            result.modified.stress_score - snap.stress_score, abs=0.01
        )

    def test_delta_tier_false_when_no_change(self):
        snap = _make_snap()
        result = run_scenario(snap, "test")  # no changes
        assert result.delta_tier is False

    def test_delta_tier_true_when_tier_changes(self):
        snap = _make_low_snap()
        # From LOW → should escalate to at least ELEVATED with big deltas
        result = run_scenario(snap, "big", streamflow_pctile_delta=-50.0, drought_index_delta=+50.0)
        assert result.delta_tier is True

    def test_positive_delta_score_when_worse(self):
        snap = _make_snap()
        result = run_scenario(snap, "worse", streamflow_pctile_delta=-20.0)
        assert result.delta_score > 0.0

    def test_negative_delta_score_when_better(self):
        snap = _make_snap()
        result = run_scenario(snap, "better", streamflow_pctile_delta=+20.0)
        assert result.delta_score < 0.0


# ---------------------------------------------------------------------------
# run_named_scenario
# ---------------------------------------------------------------------------

class TestRunNamedScenario:
    @pytest.mark.parametrize("scenario_name", list(SCENARIO_DEFAULTS.keys()))
    def test_all_named_scenarios_run(self, scenario_name):
        snap = _make_snap()
        result = run_named_scenario(snap, scenario_name)
        assert isinstance(result, ScenarioResult)

    @pytest.mark.parametrize("scenario_name", list(SCENARIO_DEFAULTS.keys()))
    def test_named_scenario_name_set(self, scenario_name):
        snap = _make_snap()
        result = run_named_scenario(snap, scenario_name)
        assert result.scenario == scenario_name

    def test_drought_intensifies_increases_score(self):
        snap = _make_snap()
        result = run_named_scenario(snap, "drought_intensifies")
        assert result.delta_score > 0.0

    def test_streamflow_collapse_increases_score(self):
        snap = _make_snap()
        result = run_named_scenario(snap, "streamflow_collapse")
        assert result.delta_score > 0.0

    def test_reservoir_low_applies_override(self):
        snap = _make_snap(reservoir_pct=80.0)
        result = run_named_scenario(snap, "reservoir_low")
        assert result.modified.reservoir_pct == pytest.approx(20.0)

    def test_heat_wave_increases_score(self):
        snap = _make_snap()
        result = run_named_scenario(snap, "heat_wave")
        assert result.delta_score > 0.0

    def test_unknown_scenario_raises_value_error(self):
        snap = _make_snap()
        with pytest.raises(ValueError, match="Unknown scenario"):
            run_named_scenario(snap, "nonexistent_scenario")

    def test_all_scenarios_produce_valid_tier(self):
        snap = _make_snap()
        for name in SCENARIO_DEFAULTS:
            result = run_named_scenario(snap, name)
            assert result.modified.tier in {"LOW", "ELEVATED", "HIGH", "CRITICAL"}
