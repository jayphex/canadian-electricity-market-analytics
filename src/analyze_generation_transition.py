from pathlib import Path
import textwrap

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

BACKGROUND = "#F7F4EF"
TEXT = "#171717"
MUTED = "#66625D"
GRID = "#D9D4CC"
HYDRO = "#315D8C"
NUCLEAR = "#6B5BD2"
COMBUSTIBLE = "#B2861B"
WIND_SOLAR = "#2E8B6D"
OTHER = "#B2861B"


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


def apply_editorial_style(fig, ax) -> None:
    fig.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.tick_params(axis="both", colors=MUTED, length=0, labelsize=11)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def add_header(fig, title: str, subtitle: str) -> None:
    wrapped_title = textwrap.fill(title, width=58)
    wrapped_subtitle = textwrap.fill(subtitle, width=95)
    fig.text(
        0.105,
        0.94,
        wrapped_title,
        ha="left",
        va="top",
        fontsize=20,
        fontweight="bold",
        color=TEXT,
        linespacing=1.1,
    )
    title_lines = wrapped_title.count("\n") + 1
    subtitle_y = 0.865 if title_lines == 1 else 0.825
    fig.text(
        0.105,
        subtitle_y,
        wrapped_subtitle,
        ha="left",
        va="top",
        fontsize=12.5,
        color=MUTED,
        linespacing=1.15,
    )


def plot_cumulative_change(change_table: pd.DataFrame) -> Path:
    ordered = change_table.sort_values("absolute_change_million_mwh")
    color_map = {
        "Hydro": HYDRO,
        "Nuclear": NUCLEAR,
        "Combustible fuels": COMBUSTIBLE,
        "Wind + solar": WIND_SOLAR,
    }

    fig, ax = plt.subplots(figsize=(11, 6.8))
    apply_editorial_style(fig, ax)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.grid(axis="y", visible=False)

    colors = [color_map[source] for source in ordered["source"]]
    bars = ax.barh(
        ordered["source"],
        ordered["absolute_change_million_mwh"],
        color=colors,
        height=0.54,
    )
    ax.axvline(0, color=TEXT, linewidth=1.1)

    ax.set_xlim(-45, 32)
    ax.set_xlabel("Change in annual generation (million MWh)", color=MUTED, fontsize=11, labelpad=14)
    ax.set_ylabel("")

    add_header(
        fig,
        "Canada lost hydro and nuclear output while wind and solar expanded",
        "Change in annual electricity generation by source, 2016 to 2025",
    )

    for bar, value in zip(bars, ordered["absolute_change_million_mwh"]):
        y = bar.get_y() + bar.get_height() / 2
        if value < 0:
            ax.text(value - 1.2, y, f"{value:.1f}", ha="right", va="center", fontsize=12, fontweight="bold", color=TEXT)
        else:
            ax.text(value + 1.2, y, f"+{value:.1f}", ha="left", va="center", fontsize=12, fontweight="bold", color=TEXT)

    fig.text(0.105, 0.035, "Source: Statistics Canada, table 25-10-0015", fontsize=10, color=MUTED, ha="left")
    fig.text(0.895, 0.035, "CANADIAN ELECTRICITY MARKET ANALYTICS", fontsize=9, fontweight="bold", color=MUTED, ha="right")

    fig.subplots_adjust(left=0.22, right=0.91, top=0.72, bottom=0.16)
    output_path = OUTPUT_DIR / "generation_change_2016_2025.svg"
    fig.savefig(output_path, format="svg", facecolor=BACKGROUND)
    plt.close(fig)
    return output_path


def plot_annual_substitution(annual_changes: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(11, 6.8))
    apply_editorial_style(fig, ax)

    years = annual_changes["year"]
    hydro = annual_changes["hydroelectric_million_mwh"]
    other = annual_changes["other_sources_change_million_mwh"]

    ax.plot(years, hydro, color=HYDRO, linewidth=3.2)
    ax.plot(years, other, color=OTHER, linewidth=3.2)
    ax.scatter(years, hydro, color=HYDRO, s=38, zorder=3)
    ax.scatter(years, other, color=OTHER, s=38, zorder=3)
    ax.axhline(0, color=TEXT, linewidth=1.0)

    ax.set_xlim(years.min() - 0.2, years.max() + 1.45)
    ax.set_ylim(-12, 17)
    ax.set_xticks(years)
    ax.set_ylabel("Year-over-year change (million MWh)", color=MUTED, fontsize=11, labelpad=12)
    ax.set_xlabel("")

    add_header(
        fig,
        "Hydro declines were not consistently offset by other generation",
        "Annual change in hydro versus combustible fuels, nuclear, wind and solar combined, 2017 to 2025",
    )

    end_year = years.iloc[-1]
    ax.text(end_year + 0.25, hydro.iloc[-1], f"Hydro\n{hydro.iloc[-1]:+.1f}", color=HYDRO, fontsize=12, fontweight="bold", va="center")
    ax.text(end_year + 0.25, other.iloc[-1], f"Other generation\n{other.iloc[-1]:+.1f}", color=OTHER, fontsize=12, fontweight="bold", va="center")

    fig.text(0.105, 0.035, "Source: Statistics Canada, table 25-10-0015", fontsize=10, color=MUTED, ha="left")
    fig.text(0.895, 0.035, "CANADIAN ELECTRICITY MARKET ANALYTICS", fontsize=9, fontweight="bold", color=MUTED, ha="right")

    fig.subplots_adjust(left=0.12, right=0.82, top=0.72, bottom=0.15)
    output_path = OUTPUT_DIR / "hydro_vs_other_sources_annual_change.svg"
    fig.savefig(output_path, format="svg", facecolor=BACKGROUND)
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
