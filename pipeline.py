"""Orchestrates USGS streamflow + USDM drought data into WaterSnapshot objects."""
from datetime import date
from config import REGIONS
from usgs_client import fetch_streamflow
from drought_client import fetch_drought
from stress_engine import WaterSnapshot, build_snapshot


def build_snapshots(regions: list[str] | None = None) -> dict[str, WaterSnapshot]:
    """
    Returns {region: WaterSnapshot} for each requested region.

    In DEMO_MODE all data comes from seed_data; otherwise calls USGS and USDM APIs.
    """
    if regions is None:
        regions = list(REGIONS.keys())

    today = date.today().isoformat()
    result: dict[str, WaterSnapshot] = {}

    for region in regions:
        flow_data = fetch_streamflow(region)
        drought_data = fetch_drought(region)
        reservoir_pct = _get_reservoir_pct(region)

        result[region] = build_snapshot(
            region=region,
            date=today,
            streamflow_pctile=flow_data["streamflow_pctile"],
            streamflow_cfs=flow_data.get("streamflow_cfs"),
            reservoir_pct=reservoir_pct,
            drought_d0_pct=drought_data["d0_pct"],
            drought_d1_pct=drought_data["d1_pct"],
            drought_d2_pct=drought_data["d2_pct"],
            drought_d3_pct=drought_data["d3_pct"],
            drought_d4_pct=drought_data["d4_pct"],
        )

    return result


def _get_reservoir_pct(region: str) -> float | None:
    """Return demo or live reservoir storage % for regions that have one."""
    from config import DEMO_MODE
    if not REGIONS[region]["has_reservoir"]:
        return None
    if DEMO_MODE:
        from seed_data import DEMO_RESERVOIR
        return DEMO_RESERVOIR.get(region)
    # Live mode: reservoir level fetch not yet implemented — return None gracefully
    return None
