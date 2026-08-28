# Canadian Electricity Market Analytics

## Project question

**How is Canada's electricity system changing, and where are the biggest opportunities and challenges in the transition toward cleaner generation?**

## Project purpose

This project analyzes changes in Canada's electricity system using public data, with an emphasis on provincial differences, generation mix, system evolution, electricity trade, and the opportunities and constraints associated with cleaner electricity.

The project is designed as a reproducible analytics case study. Evidence is separated from interpretation, and hypotheses are tested rather than assumed.

## What is implemented

The current pipeline uses Statistics Canada's Web Data Service (WDS) to retrieve and validate monthly provincial electricity data for 2016–2025.

Implemented analysis includes:

- Provincial generation history by hydro, nuclear, wind, solar, and combustible generation
- Annual generation totals and generation-mix shares
- Coverage and StatsCan quality/status-code validation
- 2016 versus 2025 generation change comparisons
- Provincial electricity receipts and deliveries
- Local generation versus electricity available for use
- Net importer/exporter position by province
- A focused PEI case study showing why local generation mix and total electricity supply are different concepts

The pipeline preserves source vector IDs, coordinates, status codes, units, and release metadata so results can be traced back to Statistics Canada.

## Current Phase 2 visualizations

### Generation change by source, 2016–2025

![Change in Canadian electricity generation by source, 2016–2025](docs/figures/generation_change_2016_2025.svg)

Hydro and nuclear generation are lower in 2025 than in 2016, while wind and solar show substantial growth. Combustible generation is modestly higher over the same endpoint comparison.

### Annual hydro change versus other generation

![Annual hydro change versus other generation sources](docs/figures/hydro_vs_other_sources_annual_change.svg)

The year-over-year comparison tests whether changes in combustible generation, nuclear, and wind/solar collectively offset annual hydro movements. The relationship varies materially by year, so the national data should not be interpreted as a simple one-for-one substitution pattern.

## Working approach

1. Source and assess authoritative Canadian electricity datasets.
2. Define research questions and candidate hypotheses.
3. Build a clean, reproducible analytical dataset.
4. Analyze national and provincial trends.
5. Test explanations for observed changes.
6. Develop clear visualizations and an interactive dashboard.
7. Produce a concise analytical report and portfolio case study.

## Analytical areas

- Electricity generation mix over time
- Provincial differences
- Growth and decline by generation technology
- Interprovincial and international electricity trade
- Reliability, resilience, and system constraints
- Demand growth and electrification
- Transition opportunities and challenges

## Repository structure

```text
canadian-electricity-market-analytics/
├── data/
│   ├── raw/            # Original source files; never manually edited
│   └── processed/      # Cleaned analytical datasets
├── notebooks/          # Exploratory analysis and validation
├── src/                # Reusable Python data and analysis code
├── dashboard/          # Dashboard application and assets
├── report/             # Final analytical report materials
├── docs/               # Research notes, data dictionary, methodology
├── requirements.txt
└── README.md
```

## Data principles

- Prefer primary sources such as Statistics Canada, the Canada Energy Regulator, Environment and Climate Change Canada, Natural Resources Canada, provincial system operators, and utilities.
- Keep raw data unchanged and document transformations.
- Record source URLs, table identifiers, release dates, and known limitations.
- Distinguish observed results from interpretation.
- Follow the evidence even when results complicate the initial hypothesis.

## Current status

**Phase 2: provincial generation and electricity-trade baseline.**

The project now has a reproducible 2016–2025 provincial generation panel and a companion receipts/deliveries panel. Current work is consolidating these datasets into province-level system profiles and testing which observed patterns represent structural transitions, temporary conditions, or trade-supported supply differences.

Next milestones are annual trajectory analysis, targeted hypothesis testing, visualizations, and a portfolio-facing analytical summary/dashboard.
