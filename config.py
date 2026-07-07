"""Water Security Stress Monitor configuration — regions, thresholds, API endpoints."""
import os
from pathlib import Path
from dotenv import load_dotenv

from demo_mode import is_demo_mode

load_dotenv()

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
DEMO_MODE: bool = is_demo_mode()
MODEL: str = os.getenv("WATER_MODEL", "claude-haiku-4-5-20251001")

USGS_BASE = "https://waterservices.usgs.gov/nwis"
DROUGHT_BASE = "https://usdmdataservices.unl.edu/api"
USER_AGENT = "WaterMonitor/1.0 (portfolio; contact jak.potvin@gmail.com)"

# primary_station: USGS gauge site ID for representative streamflow
# normal_flow_cfs: approximate long-term median discharge at primary station
# has_reservoir: whether region has a major managed reservoir to track storage
REGIONS: dict[str, dict] = {
    "COLO": {
        "name": "Colorado River Basin",
        "states": ["CO", "UT", "AZ", "NV", "CA"],
        "primary_station": "09380000",   # Colorado R at Lee's Ferry, AZ
        "normal_flow_cfs": 13500.0,
        "reservoir_name": "Lake Mead/Powell",
        "has_reservoir": True,
    },
    "CAL": {
        "name": "California",
        "states": ["CA"],
        "primary_station": "11447650",   # Sacramento R at Freeport
        "normal_flow_cfs": 18000.0,
        "reservoir_name": "Shasta",
        "has_reservoir": True,
    },
    "SWUS": {
        "name": "Southwest",
        "states": ["AZ", "NM"],
        "primary_station": "09430500",   # Gila R near Safford, AZ
        "normal_flow_cfs": 750.0,
        "reservoir_name": None,
        "has_reservoir": False,
    },
    "SPLNS": {
        "name": "Southern Plains",
        "states": ["TX", "OK", "KS"],
        "primary_station": "07303000",   # Red R near Wellington, TX
        "normal_flow_cfs": 1400.0,
        "reservoir_name": None,
        "has_reservoir": False,
    },
    "GPLN": {
        "name": "Great Plains",
        "states": ["KS", "NE", "SD", "ND"],
        "primary_station": "06610000",   # Missouri R at Sioux City, IA
        "normal_flow_cfs": 32000.0,
        "reservoir_name": "Garrison/Oahe",
        "has_reservoir": True,
    },
    "GLAKE": {
        "name": "Great Lakes",
        "states": ["MI", "WI", "IN", "OH"],
        "primary_station": "04085427",   # Lake Michigan at Milwaukee, WI
        "normal_flow_cfs": 5000.0,
        "reservoir_name": None,
        "has_reservoir": False,
    },
    "SE": {
        "name": "Southeast",
        "states": ["GA", "AL", "FL", "SC"],
        "primary_station": "02350900",   # Apalachicola R near Chattahoochee, FL
        "normal_flow_cfs": 19000.0,
        "reservoir_name": None,
        "has_reservoir": False,
    },
    "MISS": {
        "name": "Mississippi Basin",
        "states": ["MO", "IA", "IL", "MN"],
        "primary_station": "07010000",   # Mississippi R at Thebes, IL
        "normal_flow_cfs": 180000.0,
        "reservoir_name": None,
        "has_reservoir": False,
    },
}

# STRESS_TIERS moved to stress_core.py (Phase 6, Cluster 5 consistency pass) --
# was a byte-identical duplicate of gridpulse's own copy; see stress_core.py.

# USDM drought severity multipliers (D0=1 through D4=5, normalized to 0-100 scale)
DROUGHT_WEIGHTS: tuple[float, ...] = (1.0, 2.0, 3.0, 4.0, 5.0)

# what-if scenarios applied to current snapshot inputs
SCENARIO_DEFAULTS: dict[str, dict] = {
    "drought_intensifies":  {"drought_index_delta": +25.0, "streamflow_pctile_delta": -10.0},
    "streamflow_collapse":  {"drought_index_delta":  +5.0, "streamflow_pctile_delta": -40.0},
    "reservoir_low":        {"drought_index_delta": +10.0, "streamflow_pctile_delta": -15.0, "reservoir_pct_override": 20.0},
    "heat_wave":            {"drought_index_delta": +20.0, "streamflow_pctile_delta": -20.0},
}

# CISA National Critical Function framing
NCF_LABEL = "Provide Potable Water / Manage Wastewater"
NCF_ID = "NCF-39/40"
