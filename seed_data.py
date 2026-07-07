"""
Pre-seeded demo data for all 8 water regions (as of 2026-06-24).

Demo stress tiers:
  COLO:  CRITICAL (82.8) -- Lake Mead/Powell storage crisis + exceptional drought
  CAL:   HIGH     (53.3) -- dry water year, Shasta at 55%, persistent drought
  SWUS:  CRITICAL (84.9) -- near-zero Gila flow + exceptional drought coverage
  SPLNS: ELEVATED (40.7) -- moderate drought, slightly below-normal Red River
  GPLN:  LOW      (15.8) -- strong Missouri flow, reservoirs full after wet winter
  GLAKE: LOW       (9.2) -- abundant Great Lakes levels, minimal drought
  SE:    ELEVATED (44.2) -- below-normal Apalachicola, persistent Georgia drought
  MISS:  LOW      (24.0) -- near-normal Mississippi flow, minimal drought
"""

# ---------------------------------------------------------------------------
# USGS streamflow data per region
# ---------------------------------------------------------------------------

DEMO_STREAMFLOW: dict[str, dict] = {
    "COLO":  {"streamflow_cfs":  2800.0,  "streamflow_pctile":  5.0},
    "CAL":   {"streamflow_cfs": 11200.0,  "streamflow_pctile": 18.0},
    "SWUS":  {"streamflow_cfs":    18.0,  "streamflow_pctile":  3.0},
    "SPLNS": {"streamflow_cfs":   820.0,  "streamflow_pctile": 35.0},
    "GPLN":  {"streamflow_cfs": 46500.0,  "streamflow_pctile": 68.0},
    "GLAKE": {"streamflow_cfs":  5900.0,  "streamflow_pctile": 82.0},
    "SE":    {"streamflow_cfs": 12100.0,  "streamflow_pctile": 30.0},
    "MISS":  {"streamflow_cfs": 193000.0, "streamflow_pctile": 58.0},
}

# ---------------------------------------------------------------------------
# Reservoir storage per region (% of total capacity)
# Only for regions with has_reservoir=True
# ---------------------------------------------------------------------------

DEMO_RESERVOIR: dict[str, float | None] = {
    "COLO":  25.0,   # Lake Mead/Powell combined at historic low
    "CAL":   55.0,   # Shasta at 55% after dry winter
    "SWUS":  None,
    "SPLNS": None,
    "GPLN":  78.0,   # Garrison/Oahe reservoirs well-filled
    "GLAKE": None,
    "SE":    None,
    "MISS":  None,
}

# ---------------------------------------------------------------------------
# USDM drought data — cumulative area percentages (d0 includes d1+d2+d3+d4)
# ---------------------------------------------------------------------------

DEMO_DROUGHT: dict[str, dict] = {
    "COLO":  {"d0_pct": 98.0, "d1_pct": 95.0, "d2_pct": 88.0, "d3_pct": 72.0, "d4_pct": 40.0},
    "CAL":   {"d0_pct": 80.0, "d1_pct": 60.0, "d2_pct": 40.0, "d3_pct": 15.0, "d4_pct":  2.0},
    "SWUS":  {"d0_pct": 99.0, "d1_pct": 95.0, "d2_pct": 85.0, "d3_pct": 60.0, "d4_pct": 25.0},
    "SPLNS": {"d0_pct": 45.0, "d1_pct": 25.0, "d2_pct": 10.0, "d3_pct":  2.0, "d4_pct":  0.0},
    "GPLN":  {"d0_pct": 12.0, "d1_pct":  5.0, "d2_pct":  1.0, "d3_pct":  0.0, "d4_pct":  0.0},
    "GLAKE": {"d0_pct":  2.0, "d1_pct":  0.0, "d2_pct":  0.0, "d3_pct":  0.0, "d4_pct":  0.0},
    "SE":    {"d0_pct": 50.0, "d1_pct": 28.0, "d2_pct": 12.0, "d3_pct":  2.0, "d4_pct":  0.0},
    "MISS":  {"d0_pct": 20.0, "d1_pct":  8.0, "d2_pct":  2.0, "d3_pct":  0.0, "d4_pct":  0.0},
}

# ---------------------------------------------------------------------------
# Pre-baked stress briefs for demo mode
# ---------------------------------------------------------------------------

DEMO_BRIEFS: dict[str, str] = {
    "COLO": (
        "The Colorado River Basin is in CRITICAL water stress driven by the sustained "
        "multi-decade overallocation of the river combined with 22 years of drought. "
        "Lee's Ferry streamflow is at the 5th percentile -- among the lowest recorded -- "
        "while Lake Mead and Powell sit at just 25% combined storage capacity. "
        "With 98% of the basin in D0+ drought and 40% in exceptional D4 conditions, "
        "any further below-normal precipitation will accelerate the storage decline "
        "and threaten the reliability of the 1922 Colorado River Compact allocations."
    ),
    "CAL": (
        "California is in HIGH water stress following a below-average water year. "
        "Sacramento River flow is at the 18th percentile, and Shasta Reservoir stands at "
        "55% of capacity -- well below normal for this point in the season. "
        "Persistent drought covers 80% of the state, with 40% in severe D2+ conditions. "
        "Urban and agricultural demand are elevated ahead of peak summer, and without "
        "above-normal fall precipitation, reservoir drawdowns will continue through winter."
    ),
    "SWUS": (
        "The Southwest is in CRITICAL water stress with near-record low streamflow on the "
        "Gila River (3rd percentile) and 99% of the region in drought -- 25% at the "
        "exceptional D4 level. Combined with no major reservoir buffer, the region has "
        "virtually no storage resilience against extended dry periods. "
        "Municipal systems dependent on groundwater are under increasing pressure as "
        "surface water becomes unavailable for recharge."
    ),
    "SPLNS": (
        "The Southern Plains are in ELEVATED water stress. Red River discharge is at the "
        "35th percentile -- below normal but not alarming -- while moderate drought (D1+) "
        "covers 25% of the region. Soil moisture deficits from the preceding dry months "
        "are limiting groundwater recharge. Stress is manageable but trending upward if "
        "summer heat persists without significant rainfall."
    ),
    "GPLN": (
        "The Great Plains are in LOW water stress following a wet winter and spring. "
        "Missouri River flow is at the 68th percentile, and the Garrison and Oahe "
        "reservoirs are at 78% capacity. Drought coverage is minimal at 12% in D0 "
        "conditions only. The region is well-positioned to handle summer demand, "
        "though prolonged summer heat could erode the current water surplus."
    ),
    "GLAKE": (
        "The Great Lakes region is in LOW water stress with streamflow at the 82nd "
        "percentile -- well above normal. Lake levels remain high, and only 2% of the "
        "region shows any abnormal dryness. Water supply for municipal, industrial, and "
        "navigation users is not under pressure. This region represents one of the "
        "largest surface freshwater reservoirs in North America with strong current conditions."
    ),
    "SE": (
        "The Southeast is in ELEVATED water stress after a dry spring reduced Apalachicola "
        "River flow to the 30th percentile. Half the region is in D0+ drought, with 12% "
        "in severe D2 conditions centered on north Georgia and Alabama. "
        "Interstate water conflicts over Apalachicola-Chattahoochee-Flint basin allocations "
        "are active. Without above-normal summer precipitation, reservoir levels in the "
        "ACF system could decline further heading into fall."
    ),
    "MISS": (
        "The Mississippi Basin is in LOW water stress with flow at the 58th percentile -- "
        "near normal for this season. Drought affects only 20% of the basin at the D0 "
        "threshold. Navigation conditions on the main stem are normal. Agricultural "
        "water demand is moderate and well within available supply margins. "
        "No immediate stress drivers are present, though isolated sub-basin drought "
        "conditions in the upper Midwest warrant continued monitoring."
    ),
    "_default": (
        "Water stress data is available in demo mode. "
        "Set DEMO_MODE=False to generate live stress briefs "
        "from real USGS streamflow and USDM drought data."
    ),
}
