"""Tests for drought_client.py — USDM drought data fetching."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from drought_client import fetch_drought, _latest_tuesday
from config import REGIONS


# ---------------------------------------------------------------------------
# _latest_tuesday
# ---------------------------------------------------------------------------

class TestLatestTuesday:
    def test_returns_string(self):
        result = _latest_tuesday()
        assert isinstance(result, str)

    def test_format_yyyy_mm_dd(self):
        result = _latest_tuesday()
        parts = result.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4  # year
        assert len(parts[1]) == 2  # month
        assert len(parts[2]) == 2  # day

    def test_result_is_parseable_date(self):
        from datetime import date
        result = _latest_tuesday()
        parsed = date.fromisoformat(result)
        assert parsed.weekday() == 1  # Tuesday


# ---------------------------------------------------------------------------
# fetch_drought (demo mode)
# ---------------------------------------------------------------------------

class TestFetchDrought:
    @pytest.mark.parametrize("region", list(REGIONS.keys()))
    def test_returns_dict(self, region):
        result = fetch_drought(region)
        assert isinstance(result, dict)

    @pytest.mark.parametrize("region", list(REGIONS.keys()))
    def test_has_all_d_keys(self, region):
        result = fetch_drought(region)
        for key in ("d0_pct", "d1_pct", "d2_pct", "d3_pct", "d4_pct"):
            assert key in result

    @pytest.mark.parametrize("region", list(REGIONS.keys()))
    def test_values_in_range(self, region):
        result = fetch_drought(region)
        for key in ("d0_pct", "d1_pct", "d2_pct", "d3_pct", "d4_pct"):
            assert 0.0 <= result[key] <= 100.0

    @pytest.mark.parametrize("region", list(REGIONS.keys()))
    def test_cumulative_ordering(self, region):
        result = fetch_drought(region)
        # d0 >= d1 >= d2 >= d3 >= d4 (cumulative: worse = subset of less-severe)
        assert result["d0_pct"] >= result["d1_pct"]
        assert result["d1_pct"] >= result["d2_pct"]
        assert result["d2_pct"] >= result["d3_pct"]
        assert result["d3_pct"] >= result["d4_pct"]

    def test_colo_has_high_drought(self):
        result = fetch_drought("COLO")
        assert result["d0_pct"] > 80.0

    def test_glake_has_minimal_drought(self):
        result = fetch_drought("GLAKE")
        assert result["d0_pct"] < 20.0

    def test_swus_has_exceptional_drought(self):
        result = fetch_drought("SWUS")
        assert result["d4_pct"] > 0.0

    def test_gpln_low_drought(self):
        result = fetch_drought("GPLN")
        assert result["d2_pct"] < 20.0

    def test_returns_floats(self):
        result = fetch_drought("CAL")
        for key in ("d0_pct", "d1_pct", "d2_pct", "d3_pct", "d4_pct"):
            assert isinstance(result[key], float)
