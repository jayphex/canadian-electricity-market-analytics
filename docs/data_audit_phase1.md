# Phase 1 Data Audit: Provincial Electricity Generation

## Status

**Provisional audit. Do not use this file as the final analytical dataset.**

The preferred source remains Statistics Canada Table 25-10-0015-01. The official bulk ZIP repeatedly timed out during this audit. To continue schema and category validation without inventing data, this audit uses a transparent open-source mirror whose pipeline downloads and transforms the same StatsCan table.

Mirror reviewed: Canada Observatory (`CanadaObservatory/canada-observatory`). Its electricity pipeline identifies Statistics Canada Tables 25-10-0015-01 and 25-10-0084-01 as the sources.

## What the audit confirms about Table 25-10-0015-01

The core raw columns used by the mirror are:

- `REF_DATE`
- `GEO`
- `Class of electricity producer`
- `Type of electricity generation`
- `VALUE`

For province-level totals, the pipeline filters `Class of electricity producer` to `Total all classes of electricity producer`.

The generation categories mapped directly from Table 25-10-0015-01 are:

- `Hydraulic turbine` -> Hydro
- `Nuclear steam turbine` -> Nuclear
- `Wind power turbine` -> Wind
- `Solar` -> Solar
- `Total electricity production from biomass` -> Biomass
- `Total electricity production from non-renewable combustible fuels` -> Fossil

This is an important limitation: Table 25-10-0015-01 identifies non-renewable combustible generation as an aggregate. It does **not** by itself cleanly separate that output into coal, natural gas, and oil.

## Temporary fossil-fuel split

The mirror uses Statistics Canada Table 25-10-0084-01 to estimate the coal / natural-gas / oil composition of the non-renewable combustible total. The latest 12 months of generation in the mirror run cover **June 2025 through May 2026**, while the fossil split uses the latest annual fuel shares available to that pipeline.

Because the two source periods differ, coal/gas/oil values in `data/interim/provincial_mix_latest12m_audit.csv` should be treated as **audit estimates**, not final measured monthly source totals.

## Current provincial snapshot

The provisional latest-12-month mix shows several clearly different provincial system types:

- Hydro-dominant: Quebec, Manitoba, Newfoundland and Labrador, British Columbia.
- Nuclear-heavy: Ontario; New Brunswick also has a material nuclear share.
- Fossil-heavy: Saskatchewan, Alberta, Nova Scotia.
- Mixed system: New Brunswick.
- Wind-heavy local generation: Prince Edward Island. This does not by itself describe PEI's total electricity consumption because imports are outside this generation-only table.

These are observations only. They do not establish which provincial transition pathway is preferable or what caused each mix.

## Data-quality and interpretation flags

1. **Generation is not capacity.** A technology can have installed capacity that is used infrequently.
2. **Generation is not consumption.** Provincial imports/exports are excluded from this table.
3. **Zeros require validation.** The official table notes that not all geography x producer x generation-type combinations are available. Final raw-data processing must distinguish true zeroes from unavailable/suppressed observations.
4. **Combustible fuels require a second source** if we want coal/gas/oil separately.
5. **Latest-12-month values are not calendar-year values.** They should not be mixed with the existing 2016-2025 annual national extract without clearly labelling the periods.
6. **PEI is a warning case.** Very high wind share of local generation does not mean the province is electrically self-sufficient.
7. Territories are excluded from this first provincial comparison and should be assessed separately if included in the final scope.

## Working classification recommendation

Keep the granular technologies first, then derive multiple analytical groupings rather than choosing one irreversible classification:

### Technology-level
Hydro / Nuclear / Wind / Solar / Biomass / Coal / Natural gas / Oil

### Emissions-oriented
- Low-carbon/non-emitting proxy: Hydro + Nuclear + Wind + Solar
- Biomass: keep separate initially because treatment depends on the emissions question
- Fossil: Coal + Natural gas + Oil

### Renewable-oriented
- Renewable: Hydro + Wind + Solar + Biomass (subject to definition used)
- Nuclear: separate
- Fossil: Coal + Natural gas + Oil

This lets the project answer both renewable-transition and emissions-transition questions without incorrectly treating nuclear as fossil or renewable.

## Next required data work

1. Retrieve and preserve the complete official Table 25-10-0015-01 CSV.
2. Audit StatsCan status/symbol fields before filling missing values.
3. Produce monthly province x technology data for 2016-2025.
4. Aggregate to calendar-year province x technology totals.
5. Add Table 25-10-0016-01 only after the generation baseline is stable, to analyze imports/exports and availability.
6. Add weather/hydrology data only when testing the hydro-variability hypothesis.

## Candidate hypotheses to consider after the official historical provincial panel is built

These remain candidates, not project conclusions:

- Hydro variability is increasingly creating reliability and/or decarbonization pressure in hydro-dependent provinces.
- When hydro output falls, combustible generation and electricity imports increase.
- Canadian provinces are following structurally different electricity-transition pathways rather than converging on a single national model.
- Wind and solar growth has not yet been sufficient on its own to offset weak hydro output nationally.

The historical provincial panel should be built before accepting or rejecting any of these.
