"""Build a descriptive PEI electricity-balance summary from StatsCan Table 25-10-0016-01.

This script does not infer reliability or causality. It quantifies local generation,
receipts, deliveries, and electricity available for use within PEI's border.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

PEI = "Prince Edward Island"

REQUIRED_COMPONENTS = {
    "Total generation",
    "Total receipts",
    "Receipts from other provinces",
    "Total deliveries",
    "Deliveries to other provinces",
    "Total electricity available for use within specific geographic border",
}

OPTIONAL_US_COMPONENTS = {
    "Purchased receipts from the United States",
    "Other receipts from the United States",
    "Deliveries to the United States",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/pei_balance"))
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    df["ref_date"] = pd.to_datetime(df["ref_date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    pei = df[df["province"] == PEI].copy()
    if pei.empty:
        raise ValueError("No Prince Edward Island observations found")

    available_components = set(pei["component"].dropna())
    missing_components = REQUIRED_COMPONENTS - available_components
    if missing_components:
        raise ValueError(f"Missing required PEI components: {sorted(missing_components)}")

    if pei.duplicated(["ref_date", "component"]).any():
        raise ValueError("Duplicate PEI component-month rows found")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    coverage = (
        pei.assign(year=pei["ref_date"].dt.year)
        .groupby(["component", "year"], as_index=False)
        .agg(
            observations=("value", "size"),
            valid_months=("value", "count"),
            first_month=("ref_date", "min"),
            last_month=("ref_date", "max"),
        )
    )
    coverage.to_csv(args.output_dir / "pei_component_coverage_by_year.csv", index=False)

    status = (
        pei.assign(year=pei["ref_date"].dt.year)
        .groupby(["component", "year", "status_code"], dropna=False)
        .size().reset_index(name="months")
    )
    status.to_csv(args.output_dir / "pei_status_by_year.csv", index=False)

    annual = (
        pei.assign(year=pei["ref_date"].dt.year)
        .groupby(["year", "component"], as_index=False)["value"]
        .sum(min_count=1)
        .rename(columns={"value": "mwh"})
    )
    annual.to_csv(args.output_dir / "pei_electricity_balance_annual_long.csv", index=False)

    wide = annual.pivot(index="year", columns="component", values="mwh").reset_index()
    wide.columns.name = None

    # PEI has no StatsCan vectors for U.S. receipts/deliveries in this table.
    # Keep optional U.S. metrics as NA rather than silently inventing zero series.
    if OPTIONAL_US_COMPONENTS.issubset(available_components):
        receipts_us = (
            wide["Purchased receipts from the United States"].fillna(0)
            + wide["Other receipts from the United States"].fillna(0)
        )
        wide["receipts_from_us"] = receipts_us
        wide["net_us_receipts"] = receipts_us - wide["Deliveries to the United States"].fillna(0)
    else:
        wide["receipts_from_us"] = pd.NA
        wide["net_us_receipts"] = pd.NA

    wide["net_interprovincial_receipts"] = (
        wide["Receipts from other provinces"] - wide["Deliveries to other provinces"]
    )

    availability = wide["Total electricity available for use within specific geographic border"]
    generation = wide["Total generation"]
    total_receipts = wide["Total receipts"]

    wide["local_generation_as_pct_of_availability"] = 100 * generation / availability
    wide["gross_receipts_as_pct_of_availability"] = 100 * total_receipts / availability
    wide["net_interprovincial_receipts_as_pct_of_availability"] = (
        100 * wide["net_interprovincial_receipts"] / availability
    )
    wide["balance_check_mwh"] = (
        generation + total_receipts - wide["Total deliveries"] - availability
    )

    wide.to_csv(args.output_dir / "pei_electricity_balance_annual_wide.csv", index=False)

    print("PEI annual balance summary:")
    cols = [
        "year",
        "Total generation",
        "Total receipts",
        "Total deliveries",
        "Total electricity available for use within specific geographic border",
        "local_generation_as_pct_of_availability",
        "gross_receipts_as_pct_of_availability",
        "net_interprovincial_receipts_as_pct_of_availability",
        "balance_check_mwh",
    ]
    print(wide[cols].to_string(index=False))


if __name__ == "__main__":
    main()
