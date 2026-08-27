"""Build annual provincial electricity supply/trade balances from StatsCan 25-10-0016-01.

The analysis is descriptive. It distinguishes local generation from electricity
available for use and quantifies the net contribution of receipts less deliveries.
It does not assign an energy source to imported electricity.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REQUIRED = {
    "Total generation",
    "Total receipts",
    "Total deliveries",
    "Total electricity available for use within specific geographic border",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/processed/provincial_trade_balance")
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    df["ref_date"] = pd.to_datetime(df["ref_date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    if df["ref_date"].isna().any():
        raise ValueError("Unparseable reference dates found")
    if df.duplicated(["ref_date", "province", "component"]).any():
        raise ValueError("Duplicate province-component-month rows found")

    available = set(df["component"].dropna())
    missing = REQUIRED - available
    if missing:
        raise ValueError(f"Missing required components: {sorted(missing)}")

    core = df[df["component"].isin(REQUIRED)].copy()
    core["year"] = core["ref_date"].dt.year

    coverage = (
        core.groupby(["province", "component", "year"], as_index=False)
        .agg(months=("value", "size"), valid_months=("value", "count"))
    )
    incomplete = coverage[coverage["valid_months"] != 12]
    if not incomplete.empty:
        raise ValueError(
            "Incomplete required annual series found:\n" + incomplete.to_string(index=False)
        )

    annual_long = (
        core.groupby(["province", "year", "component"], as_index=False)["value"]
        .sum(min_count=1)
        .rename(columns={"value": "mwh"})
    )

    wide = annual_long.pivot(
        index=["province", "year"], columns="component", values="mwh"
    ).reset_index()
    wide.columns.name = None

    generation = wide["Total generation"]
    receipts = wide["Total receipts"]
    deliveries = wide["Total deliveries"]
    availability = wide[
        "Total electricity available for use within specific geographic border"
    ]

    wide["net_receipts_mwh"] = receipts - deliveries
    wide["local_generation_pct_of_availability"] = 100 * generation / availability
    wide["net_receipts_pct_of_availability"] = 100 * wide["net_receipts_mwh"] / availability
    wide["balance_check_mwh"] = generation + receipts - deliveries - availability
    wide["balance_check_pct_of_availability"] = (
        100 * wide["balance_check_mwh"] / availability
    )

    # Historical source series can contain small accounting/revision residuals.
    # Preserve and flag them instead of forcing them to zero. Fail only when a
    # discrepancy is large enough to threaten the interpretation of the balance.
    wide["balance_residual_flag"] = wide["balance_check_pct_of_availability"].abs() > 0.05
    material = wide[wide["balance_check_pct_of_availability"].abs() > 0.5]
    if not material.empty:
        raise ValueError(
            "Material provincial electricity-balance residual found:\n"
            + material[[
                "province", "year", "balance_check_mwh", "balance_check_pct_of_availability"
            ]].to_string(index=False)
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    annual_long.to_csv(args.output_dir / "provincial_trade_balance_annual_long.csv", index=False)
    wide.to_csv(args.output_dir / "provincial_trade_balance_annual.csv", index=False)

    residuals = wide[wide["balance_residual_flag"]].copy()
    residuals.to_csv(args.output_dir / "provincial_trade_balance_residuals.csv", index=False)

    snapshot = wide[wide["year"] == wide["year"].max()].copy()
    snapshot["trade_position"] = snapshot["net_receipts_mwh"].map(
        lambda x: "net importer" if x > 0 else ("net exporter" if x < 0 else "balanced")
    )
    snapshot = snapshot.sort_values("net_receipts_pct_of_availability", ascending=False)
    snapshot.to_csv(args.output_dir / "provincial_trade_balance_latest.csv", index=False)

    print(f"Validated {len(wide):,} province-year balances")
    print(f"Years: {wide['year'].min()}-{wide['year'].max()}")
    print(f"Flagged small accounting residuals: {len(residuals)}")
    print("Latest provincial electricity balance:")
    print(
        snapshot[[
            "province",
            "Total generation",
            "Total electricity available for use within specific geographic border",
            "net_receipts_mwh",
            "local_generation_pct_of_availability",
            "net_receipts_pct_of_availability",
            "trade_position",
        ]].to_string(index=False)
    )


if __name__ == "__main__":
    main()
