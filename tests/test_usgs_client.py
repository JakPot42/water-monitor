"""Tests for usgs_client.py — streamflow data and percentile estimation."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from usgs_client import estimate_percentile, fetch_streamflow
from config import REGIONS


_TYPICAL_STATS = {
    "p10": 1000.0,
    "p25": 2500.0,
    "p50": 5000.0,
    "p75": 9000.0,
    "p90": 14000.0,
}


# ---------------------------------------------------------------------------
# estimate_percentile
# ---------------------------------------------------------------------------

class TestEstimatePercentile:
    def test_at_p10_returns_10(self):
        result = estimate_percentile(1000.0, _TYPICAL_STATS)
        assert result == pytest.approx(10.0, abs=0.1)

    def test_at_p25_returns_25(self):
        result = estimate_percentile(2500.0, _TYPICAL_STATS)
        assert result == pytest.approx(25.0, abs=0.1)

    def test_at_p50_returns_50(self):
        result = estimate_percentile(5000.0, _TYPICAL_STATS)
        assert result == pytest.approx(50.0, abs=0.1)

    def test_at_p75_returns_75(self):
        result = estimate_percentile(9000.0, _TYPICAL_STATS)
        assert result == pytest.approx(75.0, abs=0.1)

    def test_at_p90_returns_90(self):
        result = estimate_percentile(14000.0, _TYPICAL_STATS)
        assert result == pytest.approx(90.0, abs=0.1)

    def test_below_p10_returns_less_than_10(self):
        result = estimate_percentile(500.0, _TYPICAL_STATS)
        assert result < 10.0

    def test_above_p90_returns_more_than_90(self):
        result = estimate_percentile(20000.0, _TYPICAL_STATS)
        assert result > 90.0

    def test_result_non_negative(self):
        result = estimate_percentile(0.0, _TYPICAL_STATS)
        assert result >= 0.0

    def test_result_at_most_100(self):
        result = estimate_percentile(999999.0, _TYPICAL_STATS)
        assert result <= 100.0

    def test_midpoint_between_p10_and_p25(self):
        mid = (1000.0 + 2500.0) / 2  # 1750
        result = estimate_percentile(mid, _TYPICAL_STATS)
        assert 10.0 < result < 25.0

    def test_midpoint_between_p25_and_p50(self):
        mid = (2500.0 + 5000.0) / 2  # 3750
        result = estimate_percentile(mid, _TYPICAL_STATS)
        assert 25.0 < result < 50.0

    def test_midpoint_between_p50_and_p75(self):
        mid = (5000.0 + 9000.0) / 2  # 7000
        result = estimate_percentile(mid, _TYPICAL_STATS)
        assert 50.0 < result < 75.0

    def test_midpoint_between_p75_and_p90(self):
        mid = (9000.0 + 14000.0) / 2  # 11500
        result = estimate_percentile(mid, _TYPICAL_STATS)
        assert 75.0 < result < 90.0

    def test_monotone_increasing(self):
        values = [0, 500, 1000, 2500, 5000, 9000, 14000, 20000]
        results = [estimate_percentile(v, _TYPICAL_STATS) for v in values]
        for i in range(len(results) - 1):
            assert results[i] <= results[i + 1]

    def test_zero_p10_returns_fallback(self):
        zero_stats = {k: 0.0 for k in _TYPICAL_STATS}
        result = estimate_percentile(100.0, zero_stats)
        assert result == pytest.approx(5.0)

    def test_returns_float(self):
        result = estimate_percentile(5000.0, _TYPICAL_STATS)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# fetch_streamflow (demo mode)
# ---------------------------------------------------------------------------

class TestFetchStreamflow:
    @pytest.mark.parametrize("region", list(REGIONS.keys()))
    def test_returns_dict(self, region):
        result = fetch_streamflow(region)
        assert isinstance(result, dict)

    @pytest.mark.parametrize("region", list(REGIONS.keys()))
    def test_has_pctile_key(self, region):
        result = fetch_streamflow(region)
        assert "streamflow_pctile" in result

    @pytest.mark.parametrize("region", list(REGIONS.keys()))
    def test_pctile_in_range(self, region):
        result = fetch_streamflow(region)
        assert 0.0 <= result["streamflow_pctile"] <= 100.0

    @pytest.mark.parametrize("region", list(REGIONS.keys()))
    def test_has_cfs_key(self, region):
        result = fetch_streamflow(region)
        assert "streamflow_cfs" in result

    def test_colo_low_percentile(self):
        result = fetch_streamflow("COLO")
        assert result["streamflow_pctile"] < 25.0

    def test_glake_high_percentile(self):
        result = fetch_streamflow("GLAKE")
        assert result["streamflow_pctile"] > 50.0

    def test_colo_has_flow_value(self):
        result = fetch_streamflow("COLO")
        assert result["streamflow_cfs"] is not None
        assert result["streamflow_cfs"] > 0
