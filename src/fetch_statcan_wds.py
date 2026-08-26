"""Fetch provincial electricity generation series from Statistics Canada's WDS API.

This avoids downloading the full Table 25-10-0015-01 ZIP. The script discovers
member IDs from table metadata, resolves coordinates to stable vector IDs, and
retrieves monthly observations through the WDS discrete-data endpoints.

Output is deliberately close to raw API data. Status/symbol/scalar metadata are
retained so that downstream cleaning can make explicit quality decisions.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests

BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest"
PRODUCT_ID = 25100015

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

TOTAL_PRODUCER = "Total all classes of electricity producer"

GENERATION_TYPES = [
    "Hydraulic turbine",
    "Nuclear steam turbine",
    "Wind power turbine",
    "Solar",
    "Total electricity production from combustible fuels",
    "Total electricity production from biomass",
    "Total electricity production from non-renewable combustible fuels",
]

TECH_LABELS = {
    "Hydraulic turbine": "Hydro",
    "Nuclear steam turbine": "Nuclear",
    "Wind power turbine": "Wind",
    "Solar": "Solar",
    "Total electricity production from combustible fuels": "Combustible fuels",
    "Total electricity production from biomass": "Biomass",
    "Total electricity production from non-renewable combustible fuels": "Non-renewable combustibles",
}


def _post(session: requests.Session, method: str, payload: list[dict[str, Any]]) -> Any:
    response = session.post(
        f"{BASE_URL}/{method}",
        json=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def get_cube_metadata(session: requests.Session) -> dict[str, Any]:
    response = _post(session, "getCubeMetadata", [{"productId": PRODUCT_ID}])
    if not response or response[0].get("status") != "SUCCESS":
        raise RuntimeError(f"StatsCan metadata request failed: {response}")
    obj = response[0]["object"]
    if obj.get("responseStatusCode") != 0:
        raise RuntimeError(f"StatsCan metadata returned non-zero status: {obj}")
    return obj


def dimension_by_name(metadata: dict[str, Any], name: str) -> dict[str, Any]:
    dimensions = metadata.get("dimension") or metadata.get("dimensions") or []
    for dimension in dimensions:
        if dimension.get("dimensionNameEn") == name:
            return dimension
    available = [d.get("dimensionNameEn") for d in dimensions]
    raise KeyError(f"Dimension '{name}' not found. Available: {available}")


def member_id(dimension: dict[str, Any], member_name: str) -> int:
    members = dimension.get("member") or dimension.get("members") or []
    for member in members:
        if member.get("memberNameEn") == member_name:
            return int(member["memberId"])
    available = [m.get("memberNameEn") for m in members]
    raise KeyError(
        f"Member '{member_name}' not found in {dimension.get('dimensionNameEn')}. "
        f"Available members include: {available}"
    )


def make_coordinate(metadata: dict[str, Any], choices: dict[str, str]) -> str:
    dimensions = metadata.get("dimension") or metadata.get("dimensions") or []
    coordinate = [0] * 10
    for dimension_name, selected_member in choices.items():
        dimension = dimension_by_name(metadata, dimension_name)
        position = int(dimension["dimensionPositionId"]) - 1
        coordinate[position] = member_id(dimension, selected_member)
    return ".".join(str(x) for x in coordinate)


def build_coordinate_requests(metadata: dict[str, Any]) -> list[dict[str, str]]:
    requests_out: list[dict[str, str]] = []
    for province, generation_type in itertools.product(PROVINCES, GENERATION_TYPES):
        coordinate = make_coordinate(
            metadata,
            {
                "Geography": province,
                "Class of electricity producer": TOTAL_PRODUCER,
                "Type of electricity generation": generation_type,
            },
        )
        requests_out.append(
            {
                "province": province,
                "generation_type": generation_type,
                "technology": TECH_LABELS[generation_type],
                "coordinate": coordinate,
            }
        )
    return requests_out


def chunks(items: list[Any], size: int) -> Iterable[list[Any]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def resolve_vectors(
    session: requests.Session, coordinate_requests: list[dict[str, str]]
) -> list[dict[str, Any]]:
    by_coordinate = {item["coordinate"]: item for item in coordinate_requests}
    resolved: list[dict[str, Any]] = []

    for batch in chunks(coordinate_requests, 50):
        payload = [
            {"productId": PRODUCT_ID, "coordinate": item["coordinate"]}
            for item in batch
        ]
        responses = _post(session, "getSeriesInfoFromCubePidCoord", payload)
        for response in responses:
            obj = response.get("object") or {}
            coordinate = str(obj.get("coordinate", ""))
            source = by_coordinate.get(coordinate)
            if response.get("status") != "SUCCESS" or obj.get("responseStatusCode") != 0:
                continue
            if source is None:
                continue
            resolved.append(
                {
                    **source,
                    "vector_id": int(obj["vectorId"]),
                    "frequency_code": obj.get("frequencyCode"),
                    "series_scalar_factor_code": obj.get("scalarFactorCode"),
                    "decimals": obj.get("decimals"),
                    "series_title": obj.get("SeriesTitleEn"),
                    "member_uom_code": obj.get("memberUomCode"),
                }
            )
    return resolved


def fetch_latest_periods(
    session: requests.Session,
    resolved: list[dict[str, Any]],
    latest_n: int = 132,
) -> pd.DataFrame:
    """Fetch enough monthly periods to cover 2016 onward, then filter locally."""
    by_vector = {int(item["vector_id"]): item for item in resolved}
    rows: list[dict[str, Any]] = []

    for batch in chunks(resolved, 50):
        payload = [
            {"vectorId": int(item["vector_id"]), "latestN": latest_n}
            for item in batch
        ]
        responses = _post(session, "getDataFromVectorsAndLatestNPeriods", payload)
        for response in responses:
            obj = response.get("object") or {}
            vector_id = obj.get("vectorId")
            if response.get("status") != "SUCCESS" or vector_id is None:
                continue
            source = by_vector.get(int(vector_id))
            if source is None:
                continue
            for point in obj.get("vectorDataPoint", []):
                rows.append(
                    {
                        "ref_date": point.get("refPerRaw") or point.get("refPer"),
                        "province": source["province"],
                        "generation_type": source["generation_type"],
                        "technology": source["technology"],
                        "value": point.get("value"),
                        "vector_id": int(vector_id),
                        "coordinate": source["coordinate"],
                        "scalar_factor_code": point.get("scalarFactorCode"),
                        "decimals": point.get("decimals"),
                        "symbol_code": point.get("symbolCode"),
                        "status_code": point.get("statusCode"),
                        "security_level_code": point.get("securityLevelCode"),
                        "release_time": point.get("releaseTime"),
                        "frequency_code": point.get("frequencyCode"),
                        "series_title": source.get("series_title"),
                        "member_uom_code": source.get("member_uom_code"),
                    }
                )

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No WDS data points were returned.")

    df["ref_date"] = pd.to_datetime(df["ref_date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.sort_values(["province", "technology", "ref_date"]).reset_index(drop=True)


def run(output_dir: Path, start_year: int, end_year: int, metadata_only: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session:
        metadata = get_cube_metadata(session)
        (output_dir / "statcan_25100015_metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        coords = build_coordinate_requests(metadata)
        pd.DataFrame(coords).to_csv(
            output_dir / "statcan_25100015_requested_coordinates.csv", index=False
        )

        if metadata_only:
            print(f"Metadata OK: {metadata.get('cubeTitleEn')}")
            print(f"Generated {len(coords)} requested province x technology coordinates.")
            return

        resolved = resolve_vectors(session, coords)
        if not resolved:
            raise RuntimeError("No requested coordinates resolved to StatsCan vectors.")
        pd.DataFrame(resolved).to_csv(
            output_dir / "statcan_25100015_resolved_vectors.csv", index=False
        )

        df = fetch_latest_periods(session, resolved)
        df = df[df["ref_date"].dt.year.between(start_year, end_year)].copy()
        if df.empty:
            raise RuntimeError(f"No data remained after filtering to {start_year}-{end_year}.")
        df.to_csv(output_dir / "statcan_25100015_wds_raw.csv", index=False)

        print(f"Resolved {len(resolved)} vectors.")
        print(f"Saved {len(df):,} monthly data points for {start_year}-{end_year}.")
        print("Status-code counts:")
        print(df["status_code"].value_counts(dropna=False).sort_index().to_string())
        print("Symbol-code counts:")
        print(df["symbol_code"].value_counts(dropna=False).sort_index().to_string())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/statcan_wds"))
    parser.add_argument("--start-year", type=int, default=2016)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--metadata-only", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.output_dir, args.start_year, args.end_year, args.metadata_only)
