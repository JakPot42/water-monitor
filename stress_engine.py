"""Deterministic water stress computation — no AI, no external calls."""
from dataclasses import dataclass
from config import STRESS_TIERS


@dataclass
class WaterSnapshot:
    region: str
    date: str
    # streamflow
    streamflow_cfs: float | None       # current discharge in cfs (None in demo for some)
    streamflow_pctile: float           # 0-100 USGS historical percentile rank
    # reservoir storage (None if region has no major managed reservoir)
    reservoir_pct: float | None        # current storage as % of total capacity
    # USDM drought coverage — cumulative percentages (D0 includes D1+D2+D3+D4)
    drought_d0_pct: float
    drought_d1_pct: float
    drought_d2_pct: float
    drought_d3_pct: float
    drought_d4_pct: float
    # derived
    drought_index: float               # 0-100, USDM weighted severity
    supply_stress: float               # 0-100, inverted supply signal
    stress_score: float                # 0-100, combined water stress index
    tier: str                          # LOW / ELEVATED / HIGH / CRITICAL


def compute_drought_index(
    d0: float, d1: float, d2: float, d3: float, d4: float
) -> float:
    """
    USDM weighted drought severity index (0-100).

    d0..d4 are CUMULATIVE area percentages (d0 includes all worse categories).
    Non-overlapping slices: D0_only = d0-d1, D1_only = d1-d2, etc.
    Weights: D0=1, D1=2, D2=3, D3=4, D4=5. Max possible = 5 (100% in D4).
    Normalized so 100% area in D4 returns 100.0.
    """
    d4_only = max(0.0, d4)
    d3_only = max(0.0, d3 - d4)
    d2_only = max(0.0, d2 - d3)
    d1_only = max(0.0, d1 - d2)
    d0_only = max(0.0, d0 - d1)
    weighted = (
        d0_only * 1.0 + d1_only * 2.0 + d2_only * 3.0 + d3_only * 4.0 + d4_only * 5.0
    ) / 5.0
    return max(0.0, min(100.0, weighted))


def compute_supply_stress(
    streamflow_pctile: float,
    reservoir_pct: float | None,
) -> float:
    """
    Supply stress component (0-100).

    Inverts streamflow percentile rank: P0 (record low) → 100, P100 (record high) → 0.
    When reservoir_pct is provided, blends: 60% streamflow stress + 40% reservoir depletion.
    """
    sf_stress = max(0.0, min(100.0, 100.0 - streamflow_pctile))
    if reservoir_pct is None:
        return sf_stress
    res_stress = max(0.0, min(100.0, 100.0 - reservoir_pct))
    return 0.6 * sf_stress + 0.4 * res_stress


def compute_water_stress(supply_stress: float, drought_index: float) -> float:
    """
    Combined water stress score (0-100).

    score = 0.5 * supply_stress + 0.5 * drought_index
    0   → abundant supply, no drought
    50  → supply at historical median, moderate drought
    100 → record-low supply, exceptional drought across the region
    """
    return max(0.0, min(100.0, 0.5 * supply_stress + 0.5 * drought_index))


def score_to_tier(score: float) -> str:
    for tier, (lo, hi) in STRESS_TIERS.items():
        if lo <= score < hi:
            return tier
    return "CRITICAL"


def build_snapshot(
    region: str,
    date: str,
    streamflow_pctile: float,
    drought_d0_pct: float,
    drought_d1_pct: float,
    drought_d2_pct: float,
    drought_d3_pct: float,
    drought_d4_pct: float,
    streamflow_cfs: float | None = None,
    reservoir_pct: float | None = None,
) -> WaterSnapshot:
    drought_index = compute_drought_index(
        drought_d0_pct, drought_d1_pct, drought_d2_pct, drought_d3_pct, drought_d4_pct
    )
    supply_stress = compute_supply_stress(streamflow_pctile, reservoir_pct)
    stress_score = compute_water_stress(supply_stress, drought_index)
    tier = score_to_tier(stress_score)
    return WaterSnapshot(
        region=region,
        date=date,
        streamflow_cfs=streamflow_cfs,
        streamflow_pctile=streamflow_pctile,
        reservoir_pct=reservoir_pct,
        drought_d0_pct=drought_d0_pct,
        drought_d1_pct=drought_d1_pct,
        drought_d2_pct=drought_d2_pct,
        drought_d3_pct=drought_d3_pct,
        drought_d4_pct=drought_d4_pct,
        drought_index=drought_index,
        supply_stress=supply_stress,
        stress_score=stress_score,
        tier=tier,
    )
