from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "statcan_25100015_national_annual_2016_2025.csv"
OUTPUT_DIR = ROOT / "docs" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_LABELS = {
    "hydroelectric_million_mwh": "Hydro",
    "combustible_fuels_million_mwh": "Combustible fuels",
    "nuclear_million_mwh": "Nuclear",
    "wind_solar_million_mwh": "Wind + solar",
}


def load_generation_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    return df.sort_values("year").reset_index(drop=True)


def build_endpoint_change_table(df: pd.DataFrame) -> pd.DataFrame:
    start = df.iloc[0]
    end = df.iloc[-1]

    rows = []
    for column, label in SOURCE_LABELS.items():
        start_value = start[column]
        end_value = end[column]
        absolute_change = end_value - start_value
        percent_change = (absolute_change / start_value) * 100
        rows.append(
            {
                "source": label,
                "start_year": int(start["year"]),
                "end_year": int(end["year"]),
                "start_million_mwh": start_value,
                "end_million_mwh": end_value,
                "absolute_change_million_mwh": absolute_change,
                "percent_change": percent_change,
            }
        )

    return pd.DataFrame(rows)


def build_annual_change_table(df: pd.DataFrame) -> pd.DataFrame:
    annual = df.copy()
    generation_columns = list(SOURCE_LABELS)
    annual[generation_columns] = annual[generation_columns].diff()
    annual = annual.dropna().reset_index(drop=True)

    annual["other_sources_change_million_mwh"] = annual[
        [
            "combustible_fuels_million_mwh",
            "nuclear_million_mwh",
            "wind_solar_million_mwh",
        ]
    ].sum(axis=1)

    return annual


def plot_cumulative_change(change_table: pd.DataFrame) -> Path:
    ordered = change_table.sort_values("absolute_change_million_mwh")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(ordered["source"], ordered["absolute_change_million_mwh"])
    ax.axvline(0, linewidth=1)
    ax.set_title("Change in Canadian electricity generation by source, 2016–2025")
    ax.set_xlabel("Change in generation (million MWh)")
    ax.set_ylabel("")
    fig.tight_layout()

    output_path = OUTPUT_DIR / "generation_change_2016_2025.svg"
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_annual_substitution(annual_changes: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(
        annual_changes["year"],
        annual_changes["hydroelectric_million_mwh"],
        marker="o",
        label="Hydro",
    )
    ax.plot(
        annual_changes["year"],
        annual_changes["other_sources_change_million_mwh"],
        marker="o",
        label="Combustible + nuclear + wind/solar",
    )
    ax.axhline(0, linewidth=1)
    ax.set_title("Annual hydro change versus other generation sources")
    ax.set_xlabel("Year")
    ax.set_ylabel("Year-over-year change (million MWh)")
    ax.legend()
    fig.tight_layout()

    output_path = OUTPUT_DIR / "hydro_vs_other_sources_annual_change.svg"
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    df = load_generation_data()
    endpoint_changes = build_endpoint_change_table(df)
    annual_changes = build_annual_change_table(df)

    endpoint_output = ROOT / "data" / "processed" / "generation_change_2016_2025.csv"
    annual_output = ROOT / "data" / "processed" / "generation_annual_changes_2017_2025.csv"

    endpoint_changes.to_csv(endpoint_output, index=False)
    annual_changes.to_csv(annual_output, index=False)

    cumulative_chart = plot_cumulative_change(endpoint_changes)
    annual_chart = plot_annual_substitution(annual_changes)

    print("Endpoint change table")
    print(endpoint_changes.to_string(index=False))
    print("\nAnnual change table")
    print(annual_changes.to_string(index=False))
    print(f"\nSaved: {endpoint_output}")
    print(f"Saved: {annual_output}")
    print(f"Saved: {cumulative_chart}")
    print(f"Saved: {annual_chart}")


if __name__ == "__main__":
    main()
