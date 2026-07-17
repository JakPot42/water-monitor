# Water Security Stress Monitor

**Water Security Stress Monitor scores how much water stress each U.S. region is under by combining live streamflow and drought data into a single index.** It fuses river-flow percentiles from the USGS with drought-severity ratings from the U.S. Drought Monitor into a 0–100 water-stress score across eight regions, with alert tiers and what-if scenarios.

## What it does

- Pulls streamflow percentile data from the USGS Water Services API (no key needed)
- Pulls D0–D4 drought severity by state from the U.S. Drought Monitor
- Combines them into a regional water-stress score (half supply-side stress, half drought severity), tiered LOW / ELEVATED / HIGH / CRITICAL
- Models what-if scenarios (drought intensifies, streamflow collapses, reservoirs run low, heat wave)
- Generates a plain-language brief explaining what's driving a region's stress, framed against the water-and-wastewater critical-infrastructure sector

Covers eight U.S. regions (Colorado, California, Southwest, Southern Plains, Great Plains, Great Lakes, Southeast, Mississippi).

## How it works

The stress index is fully deterministic and computed from the source data; Claude only narrates the result into a brief. The demo works with no API key against seeded example data.

## Usage

```bash
pip install -r requirements.txt
python main.py dashboard         # all regions at a glance
python main.py region COLO       # detail for one region
python main.py scenario SWUS     # run a what-if scenario
python main.py demo
```

## About

Water Security Stress Monitor is a command-line tool, part of a portfolio of national-security and defense-compliance software.
