"""Build a province-by-technology electricity generation panel from StatCan.

Primary input: Statistics Canada Table 25-10-0015-01 full CSV.

This module intentionally keeps the non-renewable combustible category aggregated.
Coal / natural gas / oil should only be split with a documented complementary source.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd


REQUIRED_COLUMNS = {
    "REF_DATE",
    "GEO",
    "Class of electricity producer",
    "Type of electricity generation",
    "VALUE",
}

TOTAL_PRODUCERS = "Total all classes of electricity producer"

TECH_MAP = {
    "Hydraulic turbine": "Hydro",
    "Nuclear steam turbine": "Nuclear",
    "Wind power turbine": "Wind",
    "Solar": "Solar",
    "Total electricity production from biomass": "Biomass",
    "Total electricity production from non-renewable combustible fuels": "Non-renewable combustible",
}

PROVINCES = [
    "Newfoundland and Labrador",
    "Prince Edward Island",
    "Nova Scotia",
    "New Brunswick",
    "Quebec",
    "Ontario",
    "Manitoba",
    "Saskatchewan",
    "Alberta",
    "British Columbia",
]


def load_statcan_generation(path: str | Path) -> pd.DataFrame:
    """Load the official StatsCan CSV and validate the fields used by the analysis."""
    df = pd.read_csv(path, low_memory=False)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return df


def build_monthly_panel(df: pd.DataFrame) -> pd.DataFrame:
    """Return monthly province x technology generation without filling missing values."""
    data = df[
        (df["Class of electricity producer"] == TOTAL_PRODUCERS)
        & (df["GEO"].isin(PROVINCES))
        & (df["Type of electricity generation"].isin(TECH_MAP))
    ].copy()

    data["date"] = pd.to_datetime(data["REF_DATE"], errors="coerce")
    data["generation_mwh"] = pd.to_numeric(data["VALUE"], errors="coerce")
    data["technology"] = data["Type of electricity generation"].map(TECH_MAP)

    # Do not fill missing VALUE observations with zero here. StatCan notes that not
    # all geography x producer x generation-type combinations are available.
    panel = data[["date", "GEO", "technology", "generation_mwh"]].rename(
        columns={"GEO": "province"}
    )
    return panel.sort_values(["province", "technology", "date"]).reset_index(drop=True)


def build_annual_panel(monthly: pd.DataFrame, start_year: int = 2016, end_year: int = 2025) -> pd.DataFrame:
    """Aggregate complete monthly observations to province x technology x calendar year."""
    data = monthly.copy()
    data = data[data["date"].dt.year.between(start_year, end_year)]
    data["year"] = data["date"].dt.year

    annual = (
        data.groupby(["province", "technology", "year"], as_index=False)
        .agg(
            generation_mwh=("generation_mwh", "sum"),
            observed_months=("generation_mwh", "count"),
        )
    )

    # Flag incomplete years instead of silently treating them as full-year totals.
    annual["complete_year"] = annual["observed_months"] == 12
    return annual


def data_quality_summary(monthly: pd.DataFrame) -> pd.DataFrame:
    """Summarize observation coverage before analytical aggregation."""
    x = monthly.copy()
    x["year"] = x["date"].dt.year
    return (
        x.groupby(["province", "technology", "year"], as_index=False)
        .agg(
            rows=("generation_mwh", "size"),
            non_null_values=("generation_mwh", "count"),
            missing_values=("generation_mwh", lambda s: int(s.isna().sum())),
        )
        .sort_values(["province", "technology", "year"])
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", help="Path to official 25-10-0015-01 CSV")
    parser.add_argument("--output-dir", default="data/processed")
    args = parser.parse_args()

    raw = load_statcan_generation(args.input_csv)
    monthly = build_monthly_panel(raw)
    annual = build_annual_panel(monthly)
    audit = data_quality_summary(monthly)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(out / "provincial_generation_monthly.csv", index=False)
    annual.to_csv(out / "provincial_generation_annual_2016_2025.csv", index=False)
    audit.to_csv(out / "provincial_generation_data_quality.csv", index=False)
