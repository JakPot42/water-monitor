"""Claude Haiku water stress-driver narrative brief."""
import anthropic
from config import ANTHROPIC_API_KEY, MODEL, DEMO_MODE
from stress_engine import WaterSnapshot
from scenarios import ScenarioResult


def generate_brief(
    snap: WaterSnapshot,
    scenario_result: ScenarioResult | None = None,
    *,
    demo_mode: bool = DEMO_MODE,
) -> str:
    if demo_mode:
        from seed_data import DEMO_BRIEFS
        return DEMO_BRIEFS.get(snap.region, DEMO_BRIEFS["_default"])
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": _build_prompt(snap, scenario_result)}],
        )
        return msg.content[0].text.strip()
    except Exception as exc:
        raise RuntimeError(f"Claude API error: {exc}") from exc


def _build_prompt(snap: WaterSnapshot, scenario_result: ScenarioResult | None) -> str:
    lines = [
        "Write a 3-4 sentence plain-language brief explaining what is driving the current "
        f"water security stress level for {snap.region} ({_region_name(snap.region)}). "
        "Focus on the physical causes: streamflow conditions, reservoir status, drought severity. "
        "Reference specific data values. Frame within CISA National Critical Function context "
        "(Water and Wastewater Systems). Do not hedge with disclaimers.",
        "",
        f"Region: {snap.region} ({_region_name(snap.region)})",
        f"Stress tier: {snap.tier} (score {snap.stress_score:.1f} / 100)",
        f"Streamflow percentile: {snap.streamflow_pctile:.0f}th (USGS historical rank)",
    ]
    if snap.streamflow_cfs is not None:
        lines.append(f"Current streamflow: {snap.streamflow_cfs:,.0f} cfs")
    if snap.reservoir_pct is not None:
        lines.append(f"Reservoir storage: {snap.reservoir_pct:.0f}% of capacity")
    lines += [
        f"Drought coverage (D0+): {snap.drought_d0_pct:.0f}% of region",
        f"Severe drought (D2+): {snap.drought_d2_pct:.0f}% of region",
        f"Exceptional drought (D4): {snap.drought_d4_pct:.0f}% of region",
        f"Drought severity index: {snap.drought_index:.1f} / 100",
        f"Supply stress component: {snap.supply_stress:.1f} / 100",
    ]
    if scenario_result:
        lines += [
            "",
            f"Scenario applied: {scenario_result.scenario}",
            f"Score change: {scenario_result.delta_score:+.1f} points",
            f"New tier: {scenario_result.modified.tier}",
        ]
        if scenario_result.delta_tier:
            lines.append("(Tier escalated -- mention this in the brief.)")
    return "\n".join(lines)


def _region_name(region: str) -> str:
    from config import REGIONS
    return REGIONS.get(region, {}).get("name", region)
