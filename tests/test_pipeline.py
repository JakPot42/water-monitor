"""Tests for pipeline.py — snapshot assembly from USGS + USDM data."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pipeline import build_snapshots
from stress_engine import WaterSnapshot
from config import REGIONS


REGION_KEYS = list(REGIONS.keys())


class TestBuildSnapshots:
    def test_returns_dict(self):
        result = build_snapshots()
        assert isinstance(result, dict)

    def test_all_regions_present_by_default(self):
        result = build_snapshots()
        for region in REGION_KEYS:
            assert region in result

    def test_single_region_filter(self):
        result = build_snapshots(regions=["CAL"])
        assert set(result.keys()) == {"CAL"}

    def test_multiple_region_filter(self):
        result = build_snapshots(regions=["CAL", "COLO"])
        assert set(result.keys()) == {"CAL", "COLO"}

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_returns_water_snapshot_objects(self, region):
        result = build_snapshots(regions=[region])
        assert isinstance(result[region], WaterSnapshot)

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_stress_score_in_range(self, region):
        result = build_snapshots(regions=[region])
        assert 0.0 <= result[region].stress_score <= 100.0

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_tier_is_valid(self, region):
        result = build_snapshots(regions=[region])
        assert result[region].tier in {"LOW", "ELEVATED", "HIGH", "CRITICAL"}

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_streamflow_pctile_in_range(self, region):
        result = build_snapshots(regions=[region])
        assert 0.0 <= result[region].streamflow_pctile <= 100.0

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_drought_index_in_range(self, region):
        result = build_snapshots(regions=[region])
        assert 0.0 <= result[region].drought_index <= 100.0

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_supply_stress_in_range(self, region):
        result = build_snapshots(regions=[region])
        assert 0.0 <= result[region].supply_stress <= 100.0

    def test_regions_with_reservoirs_have_pct(self):
        result = build_snapshots()
        for region, cfg in REGIONS.items():
            if cfg["has_reservoir"]:
                snap = result[region]
                assert snap.reservoir_pct is not None

    def test_regions_without_reservoirs_have_none(self):
        result = build_snapshots()
        for region, cfg in REGIONS.items():
            if not cfg["has_reservoir"]:
                snap = result[region]
                assert snap.reservoir_pct is None

    def test_colo_is_critical(self):
        result = build_snapshots(regions=["COLO"])
        assert result["COLO"].tier == "CRITICAL"

    def test_glake_is_low(self):
        result = build_snapshots(regions=["GLAKE"])
        assert result["GLAKE"].tier == "LOW"

    def test_date_is_set(self):
        result = build_snapshots(regions=["MISS"])
        assert result["MISS"].date != ""

    def test_region_field_correct(self):
        result = build_snapshots(regions=["SE"])
        assert result["SE"].region == "SE"

    def test_none_regions_arg_includes_all(self):
        result = build_snapshots(regions=None)
        assert len(result) == len(REGION_KEYS)

    def test_empty_regions_list_returns_empty(self):
        result = build_snapshots(regions=[])
        assert result == {}
