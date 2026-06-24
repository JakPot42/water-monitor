"""Tests for stress_engine.py — deterministic water stress computation."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from stress_engine import (
    compute_drought_index,
    compute_supply_stress,
    compute_water_stress,
    score_to_tier,
    build_snapshot,
)


# ---------------------------------------------------------------------------
# compute_drought_index
# ---------------------------------------------------------------------------

class TestComputeDroughtIndex:
    def test_no_drought_returns_zero(self):
        assert compute_drought_index(0, 0, 0, 0, 0) == 0.0

    def test_all_d4_returns_100(self):
        # 100% in D4: d4_only=100, weighted=100*5/5=100
        assert compute_drought_index(100, 100, 100, 100, 100) == pytest.approx(100.0)

    def test_only_d0_returns_20(self):
        # d0_only=100, weighted = 100*1/5 = 20
        assert compute_drought_index(100, 0, 0, 0, 0) == pytest.approx(20.0)

    def test_only_d1_coverage(self):
        # d1_only=100, weighted = 100*2/5 = 40
        assert compute_drought_index(100, 100, 0, 0, 0) == pytest.approx(40.0)

    def test_only_d2_coverage(self):
        # d2_only=100, weighted = 100*3/5 = 60
        assert compute_drought_index(100, 100, 100, 0, 0) == pytest.approx(60.0)

    def test_only_d3_coverage(self):
        # d3_only=100, weighted = 100*4/5 = 80
        assert compute_drought_index(100, 100, 100, 100, 0) == pytest.approx(80.0)

    def test_cumulative_values_handled(self):
        # d0=98, d1=95, d2=88, d3=72, d4=40 (COLO demo scenario)
        result = compute_drought_index(98, 95, 88, 72, 40)
        assert result == pytest.approx(78.6, abs=0.5)

    def test_result_clamped_at_100(self):
        result = compute_drought_index(100, 100, 100, 100, 100)
        assert result <= 100.0

    def test_result_non_negative(self):
        result = compute_drought_index(0, 0, 0, 0, 0)
        assert result >= 0.0

    def test_negative_inputs_clamped(self):
        result = compute_drought_index(-10, -5, 0, 0, 0)
        assert result >= 0.0

    def test_higher_severity_gives_higher_index(self):
        low = compute_drought_index(30, 0, 0, 0, 0)
        high = compute_drought_index(30, 20, 10, 5, 2)
        assert high > low

    def test_partial_d4_scenario(self):
        # 50% in D4, rest normal
        result = compute_drought_index(50, 50, 50, 50, 50)
        assert 0 < result < 100

    def test_typical_moderate_drought(self):
        # 45% d0, 25% d1, 10% d2, 2% d3, 0 d4 (SPLNS)
        result = compute_drought_index(45, 25, 10, 2, 0)
        assert result == pytest.approx(16.4, abs=0.5)

    def test_returns_float(self):
        assert isinstance(compute_drought_index(50, 30, 10, 0, 0), float)

    def test_symmetry_cumulative_vs_nonoverlapping(self):
        # Same severity, one expressed cumulatively, one by exact percentages
        # d0=50 (only), d1=0 means 50 in just D0
        r1 = compute_drought_index(50, 0, 0, 0, 0)
        # Explicit: 50 in D0 only
        assert r1 == pytest.approx(10.0)  # 50*1/5

    def test_maximum_practical_scenario(self):
        result = compute_drought_index(99, 95, 85, 60, 25)
        assert 70.0 <= result <= 100.0


# ---------------------------------------------------------------------------
# compute_supply_stress
# ---------------------------------------------------------------------------

class TestComputeSupplyStress:
    def test_median_flow_no_reservoir(self):
        # P50 → supply_stress = 50
        assert compute_supply_stress(50.0, None) == pytest.approx(50.0)

    def test_record_low_flow_no_reservoir(self):
        # P0 → supply_stress = 100
        assert compute_supply_stress(0.0, None) == pytest.approx(100.0)

    def test_record_high_flow_no_reservoir(self):
        # P100 → supply_stress = 0
        assert compute_supply_stress(100.0, None) == pytest.approx(0.0)

    def test_above_normal_flow_no_reservoir(self):
        # P82 → supply_stress = 18 (GLAKE scenario)
        assert compute_supply_stress(82.0, None) == pytest.approx(18.0)

    def test_reservoir_full_reduces_stress(self):
        # Same percentile, full reservoir should reduce stress vs no reservoir
        without = compute_supply_stress(50.0, None)
        with_full = compute_supply_stress(50.0, 100.0)
        assert with_full < without

    def test_empty_reservoir_increases_stress(self):
        without = compute_supply_stress(50.0, None)
        with_empty = compute_supply_stress(50.0, 0.0)
        assert with_empty > without

    def test_reservoir_blend_formula(self):
        # P5 + 25% reservoir (COLO scenario)
        sf_stress = 100 - 5  # = 95
        res_stress = 100 - 25  # = 75
        expected = 0.6 * 95 + 0.4 * 75  # = 87
        result = compute_supply_stress(5.0, 25.0)
        assert result == pytest.approx(expected, abs=0.1)

    def test_result_always_between_0_and_100_no_reservoir(self):
        for pctile in [0, 10, 25, 50, 75, 90, 100]:
            result = compute_supply_stress(float(pctile), None)
            assert 0.0 <= result <= 100.0

    def test_result_always_between_0_and_100_with_reservoir(self):
        for pctile in [0, 50, 100]:
            for res in [0.0, 50.0, 100.0]:
                result = compute_supply_stress(float(pctile), res)
                assert 0.0 <= result <= 100.0

    def test_higher_percentile_lower_stress(self):
        low_pctile = compute_supply_stress(10.0, None)
        high_pctile = compute_supply_stress(80.0, None)
        assert high_pctile < low_pctile

    def test_none_reservoir_same_as_no_blend(self):
        r1 = compute_supply_stress(40.0, None)
        # None path should return sf_stress directly = 100 - 40 = 60
        assert r1 == pytest.approx(60.0)

    def test_great_plains_scenario(self):
        # P68 + 78% reservoir (GPLN scenario)
        sf_stress = 100 - 68  # = 32
        res_stress = 100 - 78  # = 22
        expected = 0.6 * 32 + 0.4 * 22  # = 28
        result = compute_supply_stress(68.0, 78.0)
        assert result == pytest.approx(expected, abs=0.1)


# ---------------------------------------------------------------------------
# compute_water_stress
# ---------------------------------------------------------------------------

class TestComputeWaterStress:
    def test_zero_inputs_returns_zero(self):
        assert compute_water_stress(0.0, 0.0) == 0.0

    def test_max_inputs_returns_100(self):
        assert compute_water_stress(100.0, 100.0) == pytest.approx(100.0)

    def test_equal_weight_formula(self):
        # 0.5 * 60 + 0.5 * 40 = 50
        assert compute_water_stress(60.0, 40.0) == pytest.approx(50.0)

    def test_result_clamped_at_100(self):
        assert compute_water_stress(120.0, 120.0) == 100.0

    def test_result_non_negative(self):
        assert compute_water_stress(0.0, 0.0) >= 0.0

    def test_supply_only_stress(self):
        # drought_index = 0, supply = 80
        assert compute_water_stress(80.0, 0.0) == pytest.approx(40.0)

    def test_drought_only_stress(self):
        # supply = 0, drought = 80
        assert compute_water_stress(0.0, 80.0) == pytest.approx(40.0)

    def test_symmetric_inputs(self):
        # same weights → order doesn't matter
        assert compute_water_stress(70.0, 30.0) == compute_water_stress(30.0, 70.0)

    def test_colo_scenario(self):
        result = compute_water_stress(87.0, 78.6)
        assert result == pytest.approx(82.8, abs=0.5)


# ---------------------------------------------------------------------------
# score_to_tier
# ---------------------------------------------------------------------------

class TestScoreToTier:
    @pytest.mark.parametrize("score,expected", [
        (0.0,   "LOW"),
        (12.5,  "LOW"),
        (24.9,  "LOW"),
        (25.0,  "ELEVATED"),
        (37.5,  "ELEVATED"),
        (49.9,  "ELEVATED"),
        (50.0,  "HIGH"),
        (62.5,  "HIGH"),
        (74.9,  "HIGH"),
        (75.0,  "CRITICAL"),
        (87.5,  "CRITICAL"),
        (100.0, "CRITICAL"),
    ])
    def test_tier_boundaries(self, score, expected):
        assert score_to_tier(score) == expected

    def test_returns_string(self):
        assert isinstance(score_to_tier(50.0), str)


# ---------------------------------------------------------------------------
# build_snapshot
# ---------------------------------------------------------------------------

class TestBuildSnapshot:
    def _basic(self, **overrides):
        kwargs = dict(
            region="COLO",
            date="2026-06-24",
            streamflow_pctile=5.0,
            drought_d0_pct=98.0,
            drought_d1_pct=95.0,
            drought_d2_pct=88.0,
            drought_d3_pct=72.0,
            drought_d4_pct=40.0,
        )
        kwargs.update(overrides)
        return build_snapshot(**kwargs)

    def test_region_field_set(self):
        snap = self._basic()
        assert snap.region == "COLO"

    def test_date_field_set(self):
        snap = self._basic()
        assert snap.date == "2026-06-24"

    def test_streamflow_pctile_preserved(self):
        snap = self._basic(streamflow_pctile=18.0)
        assert snap.streamflow_pctile == 18.0

    def test_streamflow_cfs_none_by_default(self):
        snap = self._basic()
        assert snap.streamflow_cfs is None

    def test_streamflow_cfs_set_when_provided(self):
        snap = self._basic(streamflow_cfs=2800.0)
        assert snap.streamflow_cfs == 2800.0

    def test_reservoir_pct_none_by_default(self):
        snap = self._basic()
        assert snap.reservoir_pct is None

    def test_reservoir_pct_set_when_provided(self):
        snap = self._basic(reservoir_pct=25.0)
        assert snap.reservoir_pct == 25.0

    def test_drought_d0_preserved(self):
        snap = self._basic()
        assert snap.drought_d0_pct == 98.0

    def test_drought_d4_preserved(self):
        snap = self._basic()
        assert snap.drought_d4_pct == 40.0

    def test_drought_index_computed(self):
        snap = self._basic()
        assert snap.drought_index == pytest.approx(78.6, abs=0.5)

    def test_supply_stress_no_reservoir(self):
        snap = self._basic(streamflow_pctile=5.0)
        # No reservoir → supply_stress = 100 - 5 = 95
        assert snap.supply_stress == pytest.approx(95.0)

    def test_supply_stress_with_reservoir(self):
        snap = self._basic(streamflow_pctile=5.0, reservoir_pct=25.0)
        # 0.6*95 + 0.4*75 = 87
        assert snap.supply_stress == pytest.approx(87.0, abs=0.1)

    def test_stress_score_between_0_and_100(self):
        snap = self._basic()
        assert 0.0 <= snap.stress_score <= 100.0

    def test_tier_derived_from_score(self):
        snap = self._basic()
        assert snap.tier == score_to_tier(snap.stress_score)

    def test_colo_demo_is_critical(self):
        snap = self._basic(reservoir_pct=25.0)
        assert snap.tier == "CRITICAL"

    def test_glake_demo_is_low(self):
        snap = build_snapshot(
            region="GLAKE", date="2026-06-24",
            streamflow_pctile=82.0,
            drought_d0_pct=2.0, drought_d1_pct=0.0,
            drought_d2_pct=0.0, drought_d3_pct=0.0, drought_d4_pct=0.0,
        )
        assert snap.tier == "LOW"

    def test_valid_region_accepted(self):
        snap = build_snapshot(
            region="MISS", date="2026-06-24",
            streamflow_pctile=58.0,
            drought_d0_pct=20.0, drought_d1_pct=8.0,
            drought_d2_pct=2.0, drought_d3_pct=0.0, drought_d4_pct=0.0,
        )
        assert snap.region == "MISS"
