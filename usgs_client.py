"""USGS Water Services API client — streamflow percentile. No API key required."""
import requests
from config import USGS_BASE, USER_AGENT, DEMO_MODE, REGIONS

_HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _get(url: str, params: dict | None = None) -> dict:
    resp = requests.get(url, headers=_HEADERS, params=params or {}, timeout=20)
    resp.raise_for_status()
    return resp.json()


def fetch_current_flow(site_id: str) -> float | None:
    """
    Fetch most recent instantaneous discharge (parameterCd=00060) in cfs.
    Returns None if data unavailable or site not reporting.
    """
    data = _get(f"{USGS_BASE}/iv/", {
        "format": "json",
        "sites": site_id,
        "parameterCd": "00060",
        "period": "PT2H",
    })
    try:
        series = data["value"]["timeSeries"]
        if not series:
            return None
        values = series[0]["values"][0]["value"]
        if not values:
            return None
        return float(values[-1]["value"])
    except (KeyError, IndexError, ValueError):
        return None


def fetch_daily_stats(site_id: str, month: int, day: int) -> dict | None:
    """
    Fetch USGS daily statistics (P10/P25/P50/P75/P90) for a given calendar day.
    Returns dict with keys p10, p25, p50, p75, p90 (all in cfs) or None on failure.
    """
    data = _get(f"{USGS_BASE}/stat/", {
        "format": "json",
        "sites": site_id,
        "parameterCd": "00060",
        "statReportType": "daily",
        "statTypeCd": "all",
    })
    try:
        series = data["value"]["timeSeries"]
        if not series:
            return None
        stats_by_percentile: dict[str, float] = {}
        for ts in series:
            stat_code = ts["variable"]["options"]["option"][0]["value"]
            for entry in ts["values"][0]["value"]:
                if (int(entry["qualifiers"][0]) == month
                        and int(entry.get("dateTime", "")[:10].split("-")[2]) == day):
                    stats_by_percentile[stat_code] = float(entry["value"])
                    break
        if not stats_by_percentile:
            return None
        return {
            "p10": stats_by_percentile.get("P10", 0.0),
            "p25": stats_by_percentile.get("P25", 0.0),
            "p50": stats_by_percentile.get("P50", 0.0),
            "p75": stats_by_percentile.get("P75", 0.0),
            "p90": stats_by_percentile.get("P90", 0.0),
        }
    except (KeyError, IndexError, ValueError):
        return None


def estimate_percentile(value: float, stats: dict) -> float:
    """
    Estimate percentile rank by linear interpolation between USGS P10/P25/P50/P75/P90.

    Returns 0-100. Values below P10 interpolate toward 0; above P90 toward 100.
    """
    p10, p25, p50, p75, p90 = (
        stats["p10"], stats["p25"], stats["p50"], stats["p75"], stats["p90"]
    )
    if p10 <= 0:
        return 5.0
    if value <= p10:
        return max(0.0, value / p10 * 10.0)
    if value <= p25:
        span = max(1.0, p25 - p10)
        return 10.0 + (value - p10) / span * 15.0
    if value <= p50:
        span = max(1.0, p50 - p25)
        return 25.0 + (value - p25) / span * 25.0
    if value <= p75:
        span = max(1.0, p75 - p50)
        return 50.0 + (value - p50) / span * 25.0
    if value <= p90:
        span = max(1.0, p90 - p75)
        return 75.0 + (value - p75) / span * 15.0
    return min(100.0, 90.0 + (value - p90) / max(1.0, p90) * 10.0)


def fetch_streamflow(region: str) -> dict:
    """
    Fetch streamflow data for a region.

    Returns dict with:
      streamflow_cfs: float | None
      streamflow_pctile: float (0-100)
    """
    if DEMO_MODE:
        from seed_data import DEMO_STREAMFLOW
        return DEMO_STREAMFLOW[region]

    cfg = REGIONS[region]
    site = cfg["primary_station"]
    flow = fetch_current_flow(site)
    if flow is None:
        return {"streamflow_cfs": None, "streamflow_pctile": 50.0}

    from datetime import date
    today = date.today()
    stats = fetch_daily_stats(site, today.month, today.day)
    if stats is None:
        # Fall back to normal_flow_cfs as a rough P50 estimate
        normal = cfg["normal_flow_cfs"]
        pctile = estimate_percentile(flow, {
            "p10": normal * 0.3, "p25": normal * 0.6,
            "p50": normal, "p75": normal * 1.4, "p90": normal * 1.8,
        })
        return {"streamflow_cfs": flow, "streamflow_pctile": pctile}

    pctile = estimate_percentile(flow, stats)
    return {"streamflow_cfs": flow, "streamflow_pctile": pctile}
