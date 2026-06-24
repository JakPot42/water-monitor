"""Rich terminal dashboard — ASCII-safe for Windows cp1252 console."""
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from stress_engine import WaterSnapshot
from scenarios import ScenarioResult
from config import REGIONS, NCF_LABEL, NCF_ID

console = Console()

TIER_COLORS = {
    "LOW":      "green",
    "ELEVATED": "yellow",
    "HIGH":     "red",
    "CRITICAL": "bold red",
}

_BANNER = """
[bold cyan]Water Security Stress Monitor[/bold cyan]  [dim]v1.0[/dim]
[dim]CISA NCF: {ncf_label} ({ncf_id})[/dim]
[dim]USGS streamflow percentiles + USDM drought severity index[/dim]
""".format(ncf_label=NCF_LABEL, ncf_id=NCF_ID)

# USGS percentile condition labels (mirrors USGS WaterWatch color scheme)
_PCTILE_LABELS = [
    (10,  "Much below normal"),
    (25,  "Below normal"),
    (75,  "Normal"),
    (90,  "Above normal"),
    (101, "Much above normal"),
]


def _pctile_label(pctile: float) -> str:
    for threshold, label in _PCTILE_LABELS:
        if pctile < threshold:
            return label
    return "Much above normal"


def _bar(score: float, width: int = 20) -> str:
    filled = max(0, min(width, int(score / 100.0 * width)))
    return "#" * filled + "." * (width - filled)


def print_banner() -> None:
    console.print(_BANNER)


def print_dashboard(snapshots: dict[str, WaterSnapshot]) -> None:
    """Print all-region water stress overview."""
    console.print()
    console.rule("[bold]Regional Water Stress -- Current Conditions[/bold]")
    console.print()
    console.print(
        f"  {'Region':<6}  {'Name':<22}  {'Score':>6}  {'Tier':<10}  "
        f"{'Flow Pctile':>11}  Bar"
    )
    console.print("  " + "-" * 75)
    for region, snap in snapshots.items():
        color = TIER_COLORS.get(snap.tier, "white")
        bar = _bar(snap.stress_score)
        pctile_str = f"P{snap.streamflow_pctile:.0f}"
        console.print(
            f"  [bold]{region:<6}[/bold]  {REGIONS[region]['name']:<22}  "
            f"[{color}]{snap.stress_score:>6.1f}[/{color}]  "
            f"[{color}]{snap.tier:<10}[/{color}]  "
            f"{pctile_str:>11}  [{color}]{bar}[/{color}]"
        )
    console.print()


def print_region_detail(snap: WaterSnapshot) -> None:
    """Print full detail panel for a single region."""
    color = TIER_COLORS.get(snap.tier, "white")
    name = REGIONS[snap.region]["name"]
    console.rule(f"[bold]{snap.region} ({name}) -- Water Stress Detail[/bold]")
    console.print()

    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column("Field", style="dim")
    t.add_column("Value")

    t.add_row("Date", snap.date)
    t.add_row(
        "Stress score",
        f"[{color}]{snap.stress_score:.1f} / 100  ({snap.tier})[/{color}]"
    )
    t.add_row("Supply stress", f"{snap.supply_stress:.1f} / 100")
    t.add_row("Drought index", f"{snap.drought_index:.1f} / 100")
    t.add_row("", "")
    t.add_row(
        "Streamflow",
        f"P{snap.streamflow_pctile:.0f}  [{_pctile_label(snap.streamflow_pctile)}]"
        + (f"  --  {snap.streamflow_cfs:,.0f} cfs" if snap.streamflow_cfs is not None else "")
    )
    if snap.reservoir_pct is not None:
        res_name = REGIONS[snap.region].get("reservoir_name", "Reservoir")
        t.add_row(f"{res_name}", f"{snap.reservoir_pct:.0f}% of capacity")
    t.add_row("", "")
    t.add_row("D0+ (abnormally dry)", f"{snap.drought_d0_pct:.0f}% of region")
    t.add_row("D1+ (moderate drought)", f"{snap.drought_d1_pct:.0f}%")
    t.add_row("D2+ (severe drought)", f"{snap.drought_d2_pct:.0f}%")
    t.add_row("D3+ (extreme drought)", f"{snap.drought_d3_pct:.0f}%")
    t.add_row("D4  (exceptional)", f"{snap.drought_d4_pct:.0f}%")

    console.print(t)
    console.print()


def print_scenario(result: ScenarioResult) -> None:
    """Print base vs modified comparison for a what-if scenario."""
    snap = result.base
    mod = result.modified
    base_color = TIER_COLORS.get(snap.tier, "white")
    mod_color = TIER_COLORS.get(mod.tier, "white")
    name = REGIONS[snap.region]["name"]

    console.rule(f"[bold]Scenario: {result.scenario}[/bold]")
    console.print()
    console.print(f"  Region : {snap.region} ({name})")
    console.print(f"  Date   : {snap.date}")
    console.print()
    console.print(
        f"  Base   {_bar(snap.stress_score, 15)}  "
        f"[{base_color}]{snap.stress_score:>5.1f}  {snap.tier}[/{base_color}]"
    )
    console.print(
        f"  After  {_bar(mod.stress_score, 15)}  "
        f"[{mod_color}]{mod.stress_score:>5.1f}  {mod.tier}[/{mod_color}]"
    )
    console.print(f"  Delta  {result.delta_score:+.1f} points")
    if result.delta_tier:
        console.print(
            f"  [bold yellow]Tier escalation: {snap.tier} -> {mod.tier}[/bold yellow]"
        )
    console.print()


def print_brief(region: str, text: str) -> None:
    name = REGIONS.get(region, {}).get("name", region)
    console.print(Panel(
        text,
        title=f"[bold]Water Security Brief -- {region} ({name})[/bold]",
        border_style="cyan",
    ))
    console.print()


def print_json(data: dict) -> None:
    console.print(json.dumps(data, indent=2))
