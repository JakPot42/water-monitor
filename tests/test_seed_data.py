"""Tests for seed_data.py — demo data correctness and consistency."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from seed_data import DEMO_STREAMFLOW, DEMO_DROUGHT, DEMO_RESERVOIR, DEMO_BRIEFS
from config import REGIONS
from stress_engine import build_snapshot, score_to_tier


REGION_KEYS = list(REGIONS.keys())


# ---------------------------------------------------------------------------
# DEMO_STREAMFLOW
# ---------------------------------------------------------------------------

class TestDemoStreamflow:
    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_all_regions_present(self, region):
        assert region in DEMO_STREAMFLOW

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_has_pctile_key(self, region):
        assert "streamflow_pctile" in DEMO_STREAMFLOW[region]

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_pctile_in_valid_range(self, region):
        pctile = DEMO_STREAMFLOW[region]["streamflow_pctile"]
        assert 0.0 <= pctile <= 100.0

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_has_cfs_key(self, region):
        assert "streamflow_cfs" in DEMO_STREAMFLOW[region]

    def test_colo_low_pctile(self):
        assert DEMO_STREAMFLOW["COLO"]["streamflow_pctile"] < 15.0

    def test_glake_high_pctile(self):
        assert DEMO_STREAMFLOW["GLAKE"]["streamflow_pctile"] > 70.0

    def test_swus_lowest_pctile(self):
        assert DEMO_STREAMFLOW["SWUS"]["streamflow_pctile"] < 10.0

    def test_gpln_above_normal(self):
        assert DEMO_STREAMFLOW["GPLN"]["streamflow_pctile"] > 50.0


# ---------------------------------------------------------------------------
# DEMO_DROUGHT
# ---------------------------------------------------------------------------

class TestDemoDrought:
    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_all_regions_present(self, region):
        assert region in DEMO_DROUGHT

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_has_all_keys(self, region):
        for key in ("d0_pct", "d1_pct", "d2_pct", "d3_pct", "d4_pct"):
            assert key in DEMO_DROUGHT[region]

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_values_in_range(self, region):
        row = DEMO_DROUGHT[region]
        for key in ("d0_pct", "d1_pct", "d2_pct", "d3_pct", "d4_pct"):
            assert 0.0 <= row[key] <= 100.0

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_cumulative_ordering(self, region):
        row = DEMO_DROUGHT[region]
        assert row["d0_pct"] >= row["d1_pct"]
        assert row["d1_pct"] >= row["d2_pct"]
        assert row["d2_pct"] >= row["d3_pct"]
        assert row["d3_pct"] >= row["d4_pct"]

    def test_colo_exceptional_drought(self):
        assert DEMO_DROUGHT["COLO"]["d4_pct"] > 0.0

    def test_glake_minimal_drought(self):
        assert DEMO_DROUGHT["GLAKE"]["d0_pct"] < 10.0

    def test_swus_high_d3(self):
        assert DEMO_DROUGHT["SWUS"]["d3_pct"] > 40.0

    def test_gpln_low_d2(self):
        assert DEMO_DROUGHT["GPLN"]["d2_pct"] < 10.0


# ---------------------------------------------------------------------------
# DEMO_RESERVOIR
# ---------------------------------------------------------------------------

class TestDemoReservoir:
    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_all_regions_present(self, region):
        assert region in DEMO_RESERVOIR

    def test_has_reservoir_regions_have_value(self):
        for region, cfg in REGIONS.items():
            if cfg["has_reservoir"]:
                assert DEMO_RESERVOIR[region] is not None

    def test_no_reservoir_regions_are_none(self):
        for region, cfg in REGIONS.items():
            if not cfg["has_reservoir"]:
                assert DEMO_RESERVOIR[region] is None

    def test_colo_low_reservoir(self):
        assert DEMO_RESERVOIR["COLO"] < 50.0

    def test_gpln_healthy_reservoir(self):
        assert DEMO_RESERVOIR["GPLN"] > 60.0

    def test_reservoir_pct_in_range(self):
        for region in REGION_KEYS:
            pct = DEMO_RESERVOIR[region]
            if pct is not None:
                assert 0.0 <= pct <= 100.0


# ---------------------------------------------------------------------------
# Stress consistency checks
# ---------------------------------------------------------------------------

class TestStressConsistency:
    def _build(self, region: str):
        sf = DEMO_STREAMFLOW[region]
        dr = DEMO_DROUGHT[region]
        res = DEMO_RESERVOIR[region]
        return build_snapshot(
            region=region,
            date="2026-06-24",
            streamflow_pctile=sf["streamflow_pctile"],
            streamflow_cfs=sf.get("streamflow_cfs"),
            reservoir_pct=res,
            drought_d0_pct=dr["d0_pct"],
            drought_d1_pct=dr["d1_pct"],
            drought_d2_pct=dr["d2_pct"],
            drought_d3_pct=dr["d3_pct"],
            drought_d4_pct=dr["d4_pct"],
        )

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_score_in_range(self, region):
        snap = self._build(region)
        assert 0.0 <= snap.stress_score <= 100.0

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_tier_consistent_with_score(self, region):
        snap = self._build(region)
        assert snap.tier == score_to_tier(snap.stress_score)

    def test_colo_is_critical(self):
        snap = self._build("COLO")
        assert snap.tier == "CRITICAL"

    def test_glake_is_low(self):
        snap = self._build("GLAKE")
        assert snap.tier == "LOW"

    def test_swus_is_critical(self):
        snap = self._build("SWUS")
        assert snap.tier == "CRITICAL"

    def test_gpln_is_low(self):
        snap = self._build("GPLN")
        assert snap.tier == "LOW"

    def test_cal_is_high_or_elevated(self):
        snap = self._build("CAL")
        assert snap.tier in {"HIGH", "ELEVATED"}

    def test_splns_is_elevated(self):
        snap = self._build("SPLNS")
        assert snap.tier == "ELEVATED"

    def test_se_is_elevated(self):
        snap = self._build("SE")
        assert snap.tier == "ELEVATED"

    def test_miss_is_low(self):
        snap = self._build("MISS")
        assert snap.tier == "LOW"


# ---------------------------------------------------------------------------
# DEMO_BRIEFS
# ---------------------------------------------------------------------------

class TestDemoBriefs:
    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_all_regions_have_brief(self, region):
        assert region in DEMO_BRIEFS

    def test_default_key_present(self):
        assert "_default" in DEMO_BRIEFS

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_brief_is_string(self, region):
        assert isinstance(DEMO_BRIEFS[region], str)

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_brief_nonempty(self, region):
        assert len(DEMO_BRIEFS[region]) > 50

    def test_colo_brief_mentions_critical(self):
        assert "CRITICAL" in DEMO_BRIEFS["COLO"]

    def test_glake_brief_mentions_low(self):
        assert "LOW" in DEMO_BRIEFS["GLAKE"]
