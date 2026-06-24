"""What-if scenario modifiers — deterministic adjustments to water stress inputs."""
from dataclasses import dataclass, replace
from stress_engine import WaterSnapshot, compute_supply_stress, compute_water_stress, score_to_tier
from config import SCENARIO_DEFAULTS


@dataclass
class ScenarioResult:
    scenario: str
    base: WaterSnapshot
    modified: WaterSnapshot
    delta_score: float
    delta_tier: bool


def apply_scenario(
    snap: WaterSnapshot,
    *,
    streamflow_pctile_delta: float = 0.0,
    drought_index_delta: float = 0.0,
    reservoir_pct_override: float | None = None,
) -> WaterSnapshot:
    """
    Apply what-if modifications to a WaterSnapshot and return the modified version.

    streamflow_pctile_delta: added to current percentile (negative = worse supply).
    drought_index_delta: added to current drought index (positive = more severe).
    reservoir_pct_override: replaces current reservoir_pct when provided.
    """
    new_pctile = max(0.0, min(100.0, snap.streamflow_pctile + streamflow_pctile_delta))
    new_reservoir = (
        reservoir_pct_override if reservoir_pct_override is not None else snap.reservoir_pct
    )
    new_supply = compute_supply_stress(new_pctile, new_reservoir)
    new_drought = max(0.0, min(100.0, snap.drought_index + drought_index_delta))
    new_score = compute_water_stress(new_supply, new_drought)
    new_tier = score_to_tier(new_score)

    return replace(
        snap,
        streamflow_pctile=new_pctile,
        reservoir_pct=new_reservoir,
        supply_stress=new_supply,
        drought_index=new_drought,
        stress_score=new_score,
        tier=new_tier,
    )


def run_scenario(
    snap: WaterSnapshot,
    name: str,
    *,
    streamflow_pctile_delta: float = 0.0,
    drought_index_delta: float = 0.0,
    reservoir_pct_override: float | None = None,
) -> ScenarioResult:
    modified = apply_scenario(
        snap,
        streamflow_pctile_delta=streamflow_pctile_delta,
        drought_index_delta=drought_index_delta,
        reservoir_pct_override=reservoir_pct_override,
    )
    return ScenarioResult(
        scenario=name,
        base=snap,
        modified=modified,
        delta_score=modified.stress_score - snap.stress_score,
        delta_tier=(modified.tier != snap.tier),
    )


def run_named_scenario(snap: WaterSnapshot, scenario_name: str) -> ScenarioResult:
    """Run a scenario from SCENARIO_DEFAULTS by name."""
    if scenario_name not in SCENARIO_DEFAULTS:
        raise ValueError(
            f"Unknown scenario '{scenario_name}'. Valid: {sorted(SCENARIO_DEFAULTS)}"
        )
    params = SCENARIO_DEFAULTS[scenario_name]
    return run_scenario(snap, scenario_name, **params)
