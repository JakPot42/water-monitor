"""WaterMonitor CLI — regional water security stress index from USGS + USDM data."""
import sys
import os
import json
import click

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DEMO_MODE, REGIONS, SCENARIO_DEFAULTS
from pipeline import build_snapshots
from scenarios import run_scenario, run_named_scenario
from brief import generate_brief
from dashboard import (
    console,
    print_banner,
    print_dashboard,
    print_region_detail,
    print_scenario,
    print_brief,
    print_json,
)

_REGION_CHOICES = sorted(REGIONS.keys())
_SCENARIO_CHOICES = sorted(SCENARIO_DEFAULTS.keys())


@click.group()
def cli() -> None:
    """
    Water Security Stress Monitor: fuses USGS streamflow percentiles with
    USDM drought severity into a regional water stress index.

    \b
    CISA NCF framing: Water and Wastewater Systems (NCF-39/40)
    Data sources:
      USGS Water Services API  -- streamflow percentile rank (no key)
      US Drought Monitor API   -- drought severity by region (no key)

    Set DEMO_MODE=False to fetch live data.
    """


@cli.command()
@click.option(
    "--region", "-r",
    type=click.Choice(_REGION_CHOICES, case_sensitive=False),
    multiple=True,
    help="Region(s) to include. Default: all regions.",
)
def dashboard(region: tuple[str, ...]) -> None:
    """Show all-region water stress overview."""
    print_banner()
    regions = list(region) if region else None
    snapshots = build_snapshots(regions=regions)
    print_dashboard(snapshots)
    if DEMO_MODE:
        console.print(
            "[dim]DEMO_MODE=True -- set DEMO_MODE=False for live USGS/USDM data.[/dim]"
        )


@cli.command()
@click.argument("target_region", metavar="REGION",
                type=click.Choice(_REGION_CHOICES, case_sensitive=False))
def region(target_region: str) -> None:
    """Show detailed water stress for REGION (COLO, CAL, SWUS, SPLNS, GPLN, GLAKE, SE, MISS)."""
    print_banner()
    snapshots = build_snapshots(regions=[target_region])
    snap = snapshots.get(target_region)
    if snap is None:
        console.print(f"[red]No data returned for {target_region}.[/red]")
        raise SystemExit(1)
    print_region_detail(snap)
    if DEMO_MODE:
        console.print(
            "[dim]DEMO_MODE=True -- set DEMO_MODE=False for live USGS/USDM data.[/dim]"
        )


@cli.command()
@click.argument("target_region", metavar="REGION",
                type=click.Choice(_REGION_CHOICES, case_sensitive=False))
def brief(target_region: str) -> None:
    """Generate a Claude stress-driver brief for REGION."""
    print_banner()
    snapshots = build_snapshots(regions=[target_region])
    snap = snapshots.get(target_region)
    if snap is None:
        console.print(f"[red]No data for {target_region}.[/red]")
        raise SystemExit(1)
    console.print(
        f"[dim]Generating brief for {target_region} "
        f"(stress={snap.stress_score:.1f}, tier={snap.tier})...[/dim]"
    )
    text = generate_brief(snap)
    print_brief(target_region, text)


@cli.command()
@click.argument("target_region", metavar="REGION",
                type=click.Choice(_REGION_CHOICES, case_sensitive=False))
@click.option(
    "--scenario", "-s",
    type=click.Choice(_SCENARIO_CHOICES),
    default=None,
    help="Named scenario preset.",
)
@click.option("--streamflow-delta", type=float, default=None,
              help="Streamflow percentile delta (e.g. -40 = collapse to much lower).")
@click.option("--drought-delta", type=float, default=None,
              help="Drought index delta (e.g. +25 = more severe drought).")
@click.option("--reservoir-pct", type=float, default=None,
              help="Override reservoir storage % (e.g. 20 = critically low).")
def scenario(
    target_region: str,
    scenario: str | None,
    streamflow_delta: float | None,
    drought_delta: float | None,
    reservoir_pct: float | None,
) -> None:
    """
    What-if scenario analysis for REGION.

    \b
    Examples:
      scenario COLO --scenario drought_intensifies
      scenario CAL --streamflow-delta -30 --drought-delta 20
      scenario GPLN --scenario reservoir_low
    """
    print_banner()
    snapshots = build_snapshots(regions=[target_region])
    snap = snapshots.get(target_region)
    if snap is None:
        console.print(f"[red]No data for {target_region}.[/red]")
        raise SystemExit(1)

    has_custom = any(v is not None for v in [streamflow_delta, drought_delta, reservoir_pct])

    if not has_custom and scenario is None:
        scenario = "drought_intensifies"

    if has_custom:
        name = scenario or "custom"
        result = run_scenario(
            snap, name,
            streamflow_pctile_delta=streamflow_delta or 0.0,
            drought_index_delta=drought_delta or 0.0,
            reservoir_pct_override=reservoir_pct,
        )
    else:
        result = run_named_scenario(snap, scenario)

    print_scenario(result)

    if DEMO_MODE:
        console.print(
            "[dim]DEMO_MODE=True -- set DEMO_MODE=False for live USGS/USDM data.[/dim]"
        )


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table",
              show_default=True, help="Output format.")
def export(fmt: str) -> None:
    """Export current water stress index as JSON (integration-ready format)."""
    snapshots = build_snapshots()
    data = {
        region: {
            "stress_score": round(snap.stress_score, 1),
            "tier": snap.tier,
            "streamflow_pctile": snap.streamflow_pctile,
            "drought_index": round(snap.drought_index, 1),
            "supply_stress": round(snap.supply_stress, 1),
            "reservoir_pct": snap.reservoir_pct,
            "date": snap.date,
        }
        for region, snap in snapshots.items()
    }
    if fmt == "json":
        print_json(data)
    else:
        print_banner()
        from rich.table import Table
        from rich import box
        from dashboard import TIER_COLORS
        t = Table(box=box.SIMPLE, show_header=True)
        t.add_column("Region")
        t.add_column("Score", justify="right")
        t.add_column("Tier")
        t.add_column("Flow Pctile", justify="right")
        t.add_column("Drought Idx", justify="right")
        t.add_column("Reservoir", justify="right")
        for rgn, d in sorted(data.items()):
            color = TIER_COLORS.get(d["tier"], "white")
            res = f"{d['reservoir_pct']:.0f}%" if d["reservoir_pct"] is not None else "N/A"
            t.add_row(
                rgn,
                f"{d['stress_score']:.1f}",
                f"[{color}]{d['tier']}[/{color}]",
                f"P{d['streamflow_pctile']:.0f}",
                f"{d['drought_index']:.1f}",
                res,
            )
        console.print(t)


@cli.command()
def demo() -> None:
    """
    Run all WaterMonitor commands against seeded demo data.
    No API keys required.
    """
    print_banner()
    snapshots = build_snapshots()

    console.rule("[bold]Demo 1: All-Region Dashboard[/bold]")
    print_dashboard(snapshots)

    console.rule("[bold]Demo 2: Colorado River Basin Detail[/bold]")
    print_region_detail(snapshots["COLO"])

    console.rule("[bold]Demo 3: Colorado River Basin Brief[/bold]")
    text = generate_brief(snapshots["COLO"], demo_mode=True)
    print_brief("COLO", text)

    console.rule("[bold]Demo 4: Drought Intensification Scenario (Colorado)[/bold]")
    from scenarios import run_named_scenario
    result = run_named_scenario(snapshots["COLO"], "drought_intensifies")
    print_scenario(result)

    console.rule("[bold]Demo 5: Streamflow Collapse Scenario (California)[/bold]")
    result2 = run_named_scenario(snapshots["CAL"], "streamflow_collapse")
    print_scenario(result2)
    cal_brief = generate_brief(snapshots["CAL"], demo_mode=True)
    print_brief("CAL", cal_brief)

    console.rule("[bold]Demo 6: Great Plains -- LOW Stress Region[/bold]")
    print_region_detail(snapshots["GPLN"])

    console.rule("[bold]Demo 7: JSON Export[/bold]")
    data = {
        rgn: {
            "stress_score": round(snap.stress_score, 1),
            "tier": snap.tier,
            "streamflow_pctile": snap.streamflow_pctile,
            "drought_index": round(snap.drought_index, 1),
        }
        for rgn, snap in snapshots.items()
    }
    print_json(data)

    console.print(
        "[dim]All demo output uses seeded data. Set DEMO_MODE=False for live USGS/USDM data.[/dim]"
    )


if __name__ == "__main__":
    cli()
