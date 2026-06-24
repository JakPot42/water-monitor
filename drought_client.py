"""US Drought Monitor (USDM) API client — drought severity by region. No key required."""
import requests
from datetime import date, timedelta
from config import DROUGHT_BASE, USER_AGENT, DEMO_MODE, REGIONS

_HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _get(url: str, params: dict | None = None) -> list:
    resp = requests.get(url, headers=_HEADERS, params=params or {}, timeout=20)
    resp.raise_for_status()
    return resp.json()


def _latest_tuesday() -> str:
    """USDM data releases every Tuesday. Return most recent Tuesday as YYYY-MM-DD."""
    today = date.today()
    days_since_tuesday = (today.weekday() - 1) % 7
    tuesday = today - timedelta(days=days_since_tuesday)
    return tuesday.strftime("%Y-%m-%d")


def fetch_drought_for_state(state: str, as_of: str | None = None) -> dict | None:
    """
    Fetch USDM drought statistics for a single US state abbreviation.

    Returns dict with keys d0_pct..d4_pct (cumulative percentages) or None on failure.
    USDM values are cumulative: d0_pct is % of state in D0 *or worse*.
    """
    as_of = as_of or _latest_tuesday()
    url = f"{DROUGHT_BASE}/StateStatistics/GetDroughtSeverityStatisticsByArea"
    try:
        data = _get(url, {
            "aoi": state,
            "startdate": as_of,
            "enddate": as_of,
            "statisticsType": "1",
        })
        if not data:
            return None
        row = data[0]
        return {
            "d0_pct": float(row.get("D0", 0.0)),
            "d1_pct": float(row.get("D1", 0.0)),
            "d2_pct": float(row.get("D2", 0.0)),
            "d3_pct": float(row.get("D3", 0.0)),
            "d4_pct": float(row.get("D4", 0.0)),
        }
    except (KeyError, IndexError, ValueError, requests.RequestException):
        return None


def _aggregate_states(state_list: list[str], as_of: str | None = None) -> dict:
    """
    Average USDM drought coverage across multiple states.
    Falls back to zeros on any failure.
    """
    results = []
    for state in state_list:
        row = fetch_drought_for_state(state, as_of)
        if row is not None:
            results.append(row)
    if not results:
        return {"d0_pct": 0.0, "d1_pct": 0.0, "d2_pct": 0.0, "d3_pct": 0.0, "d4_pct": 0.0}
    return {
        "d0_pct": sum(r["d0_pct"] for r in results) / len(results),
        "d1_pct": sum(r["d1_pct"] for r in results) / len(results),
        "d2_pct": sum(r["d2_pct"] for r in results) / len(results),
        "d3_pct": sum(r["d3_pct"] for r in results) / len(results),
        "d4_pct": sum(r["d4_pct"] for r in results) / len(results),
    }


def fetch_drought(region: str) -> dict:
    """
    Fetch drought conditions for a region.

    Returns dict with d0_pct..d4_pct (0-100, cumulative USDM percentages).
    """
    if DEMO_MODE:
        from seed_data import DEMO_DROUGHT
        return DEMO_DROUGHT[region]

    states = REGIONS[region]["states"]
    return _aggregate_states(states)
