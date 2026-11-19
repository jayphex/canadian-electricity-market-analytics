"""Compare Hermanville/Clearspring and PEI wind generation by April–March fiscal year."""

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MONTHLY_PATH = (
    ROOT / "data/processed/provincial_history/provincial_generation_monthly_wide.csv"
)
OUTPUT_PATH = ROOT / "data/processed/pei_balance/hermanville_wind_fiscal_comparison.csv"

# PEI Energy Corporation 2024–25 annual report, Hermanville/Clearspring Performance.
# https://www.princeedwardisland.ca/sites/default/files/c9ab/PEIECAnnualReport2024-25.pdf
# Fiscal year end, production (MWh), turbine availability (%), capacity factor (%).
HERMANVILLE = [
    (2016, 110223, 96.6, 41.8),
    (2017, 91423, 92.3, 34.8),
    (2018, 100421, 95.7, 38.2),
    (2019, 100767, 93.1, 38.3),
    (2020, 97837, 92.4, 37.1),
    (2021, 98783, 89.4, 37.6),
    (2022, 81686, 80.5, 31.1),
    (2023, 39750, 58.2, 15.1),
    (2024, 33441, 34.1, 12.7),
    (2025, 71472, 71.8, 27.2),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--monthly", type=Path, default=MONTHLY_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    monthly = pd.read_csv(args.monthly, usecols=["province", "ref_date", "Wind"])
    pei = monthly.loc[monthly["province"].eq("Prince Edward Island")].copy()
    months = pd.to_datetime(pei["ref_date"]).dt.to_period("M")
    if months.isna().any() or months.duplicated().any():
        raise ValueError("PEI wind data contain missing dates or duplicate months")
    pei["fiscal_year_end"] = months.dt.year + months.dt.month.ge(4).astype(int)

    annual = pei.groupby("fiscal_year_end")["Wind"].agg(
        pei_wind_mwh="sum", valid_months="count"
    )
    complete = annual.loc[annual["valid_months"].eq(12), ["pei_wind_mwh"]]

    farm = pd.DataFrame(
        HERMANVILLE,
        columns=[
            "fiscal_year_end",
            "hermanville_wind_mwh",
            "hermanville_availability_pct",
            "hermanville_capacity_factor_pct",
        ],
    ).set_index("fiscal_year_end")
    comparison = farm.join(complete, how="inner", validate="one_to_one").sort_index()
    if comparison.empty:
        raise ValueError("No complete PEI fiscal years overlap the Hermanville series")

    comparison["hermanville_share_of_pei_wind_pct"] = (
        100 * comparison["hermanville_wind_mwh"] / comparison["pei_wind_mwh"].where(
            comparison["pei_wind_mwh"].gt(0)
        )
    )
    comparison["rest_of_pei_wind_mwh"] = (
        comparison["pei_wind_mwh"] - comparison["hermanville_wind_mwh"]
    )
    consecutive = comparison.index.to_series().diff().eq(1)
    for column in ["pei_wind_mwh", "hermanville_wind_mwh", "rest_of_pei_wind_mwh"]:
        comparison[column.removesuffix("_mwh") + "_yoy_change_mwh"] = (
            comparison[column].diff().where(consecutive)
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(args.output)
    print(comparison.round(2).to_string())
    print(f"Saved {len(comparison)} fiscal years to {args.output}")


if __name__ == "__main__":
    main()
