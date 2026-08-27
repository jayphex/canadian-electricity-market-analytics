"""Validate and summarize the 2016-2025 provincial electricity generation panel.

Input is the near-raw WDS output produced by fetch_statcan_wds.py. This script
keeps observation from interpretation separate: it creates descriptive tables
only and does not label causal relationships.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

EXPECTED_PROVINCES = {
    "Newfoundland and Labrador", "Prince Edward Island", "Nova Scotia",
    "New Brunswick", "Quebec", "Ontario", "Manitoba", "Saskatchewan",
    "Alberta", "British Columbia",
}
EXPECTED_TECH = {
    "Hydro", "Nuclear", "Wind", "Solar", "Combustible fuels", "Biomass",
    "Non-renewable combustibles",
}
CORE_TECH = {"Hydro", "Nuclear", "Wind", "Solar", "Combustible fuels"}


def validate(df: pd.DataFrame) -> pd.DataFrame:
    required = {
        "ref_date", "province", "technology", "value", "vector_id",
        "status_code", "symbol_code",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df.copy()
    df["ref_date"] = pd.to_datetime(df["ref_date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    if df["ref_date"].isna().any():
        raise ValueError("Unparseable reference dates found")
    if df.duplicated(["ref_date", "province", "technology"]).any():
        dupes = df[df.duplicated(["ref_date", "province", "technology"], keep=False)]
        raise ValueError(f"Duplicate province-technology-month rows found: {len(dupes)}")
    if (df["value"].dropna() < 0).any():
        raise ValueError("Negative generation values found")

    unknown_provinces = set(df["province"].dropna()) - EXPECTED_PROVINCES
    unknown_tech = set(df["technology"].dropna()) - EXPECTED_TECH
    if unknown_provinces:
        raise ValueError(f"Unexpected provinces: {sorted(unknown_provinces)}")
    if unknown_tech:
        raise ValueError(f"Unexpected technologies: {sorted(unknown_tech)}")

    return df


def build_outputs(df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    dated = df.assign(year=df["ref_date"].dt.year)

    # Data-quality audit. Never silently convert missing/unavailable values to zero.
    quality = (
        df.groupby(["status_code", "symbol_code"], dropna=False)
        .size().rename("rows").reset_index()
    )
    quality.to_csv(out_dir / "wds_quality_flags.csv", index=False)

    coverage = (
        dated.groupby(["province", "technology"])
        .agg(
            first_month=("ref_date", "min"),
            last_month=("ref_date", "max"),
            observations=("value", "size"),
            non_null_values=("value", "count"),
        )
        .reset_index()
    )
    coverage.to_csv(out_dir / "provincial_history_coverage.csv", index=False)

    # Make sequential gaps visible instead of relying only on total non-null counts.
    coverage_by_year = (
        dated.groupby(["province", "technology", "year"])
        .agg(
            months_returned=("value", "size"),
            valid_months=("value", "count"),
        )
        .reset_index()
    )
    coverage_by_year.to_csv(out_dir / "provincial_history_coverage_by_year.csv", index=False)

    status_by_year = (
        dated.groupby(["province", "technology", "year", "status_code"], dropna=False)
        .size().rename("months").reset_index()
    )
    status_by_year.to_csv(out_dir / "provincial_history_status_by_year.csv", index=False)

    # Annual totals remain technology-specific; min_count=1 preserves all-missing years as NaN.
    annual = (
        dated.groupby(["year", "province", "technology"], as_index=False)["value"]
        .sum(min_count=1)
        .rename(columns={"value": "generation"})
    )
    annual.to_csv(out_dir / "provincial_generation_annual.csv", index=False)

    # Shares use mutually exclusive core categories only. Biomass and non-renewable
    # combustibles are components of Combustible fuels and would otherwise double-count.
    core_annual = annual[annual["technology"].isin(CORE_TECH)].copy()
    totals = (
        core_annual.groupby(["year", "province"], as_index=False)["generation"]
        .sum(min_count=1)
        .rename(columns={"generation": "generation_total"})
    )
    shares = core_annual.merge(totals, on=["year", "province"])
    shares["share_pct"] = 100 * shares["generation"] / shares["generation_total"]
    shares.to_csv(out_dir / "provincial_generation_shares_annual.csv", index=False)

    # Descriptive 2016-to-2025 change table for core categories only.
    wide = core_annual.pivot_table(
        index=["province", "technology"], columns="year", values="generation"
    )
    if 2016 in wide.columns and 2025 in wide.columns:
        change = wide[[2016, 2025]].reset_index()
        change["absolute_change"] = change[2025] - change[2016]
        change["pct_change"] = 100 * change["absolute_change"] / change[2016].replace(0, pd.NA)
        change.to_csv(out_dir / "generation_change_2016_2025.csv", index=False)

    # Monthly wide table retains both the historical total and 2020+ components.
    monthly = df.pivot_table(
        index=["ref_date", "province"], columns="technology", values="value", aggfunc="sum"
    ).reset_index()
    monthly.to_csv(out_dir / "provincial_generation_monthly_wide.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/provincial_history"))
    args = parser.parse_args()

    df = validate(pd.read_csv(args.input))
    build_outputs(df, args.output_dir)
    print(f"Validated {len(df):,} WDS observations and wrote descriptive outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
