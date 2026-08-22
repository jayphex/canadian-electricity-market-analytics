# Canadian Electricity Market Analytics

## Project question

**How is Canada's electricity system changing, and where are the biggest opportunities and challenges in the transition toward cleaner generation?**

## Project purpose

This project analyzes changes in Canada's electricity system using public data, with an emphasis on provincial differences, generation mix, system evolution, and the opportunities and constraints associated with cleaner electricity.

The project is designed as a reproducible analytics case study. Evidence will be separated from interpretation, and hypotheses will be tested rather than assumed.

## Working approach

1. Source and assess authoritative Canadian electricity datasets.
2. Define research questions and candidate hypotheses.
3. Build a clean, reproducible analytical dataset.
4. Analyze national and provincial trends.
5. Test explanations for observed changes.
6. Develop clear visualizations and an interactive dashboard.
7. Produce a concise analytical report and portfolio case study.

## Planned analytical areas

- Electricity generation mix over time
- Provincial and territorial differences
- Growth and decline by generation technology
- Low-carbon and fossil generation shares
- Interprovincial and international electricity trade
- Reliability, resilience, and system constraints
- Demand growth and electrification
- Transition opportunities and challenges

These areas are provisional and will be refined as datasets are reviewed and hypotheses are selected.

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

## Status

**Phase 1: data discovery and baseline design.**

The first task is to identify and validate the core datasets needed to build a province-by-province baseline of Canadian electricity generation.
