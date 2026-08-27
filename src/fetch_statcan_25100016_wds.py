"""Fetch provincial electricity receipts, deliveries, and availability from StatsCan WDS.

Source: Statistics Canada Table 25-10-0016-01.
The output stays close to the WDS response and preserves status/symbol codes.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests

BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest"
PRODUCT_ID = 25100016

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

COMPONENTS = [
    "Total generation",
    "Total receipts",
    "Receipts from other provinces",
    "Purchased receipts from the United States",
    "Other receipts from the United States",
    "Total deliveries",
    "Deliveries to other provinces",
    "Deliveries to the United States",
    "Total electricity available for use within specific geographic border",
]


def _post(session: requests.Session, method: str, payload: list[dict[str, Any]]) -> Any:
    response = session.post(
        f"{BASE_URL}/{method}",
        json=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def chunks(items: list[Any], size: int) -> Iterable[list[Any]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def get_metadata(session: requests.Session) -> dict[str, Any]:
    response = _post(session, "getCubeMetadata", [{"productId": PRODUCT_ID}])
    if not response or response[0].get("status") != "SUCCESS":
        raise RuntimeError(f"StatsCan metadata request failed: {response}")
    obj = response[0]["object"]
    if obj.get("responseStatusCode") != 0:
        raise RuntimeError(f"StatsCan metadata returned non-zero status: {obj}")
    return obj


def dimensions(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    return metadata.get("dimension") or metadata.get("dimensions") or []


def dimension_by_name(metadata: dict[str, Any], name: str) -> dict[str, Any]:
    for dimension in dimensions(metadata):
        if dimension.get("dimensionNameEn") == name:
            return dimension
    raise KeyError(f"Dimension not found: {name}")


def member_id(dimension: dict[str, Any], name: str) -> int:
    members = dimension.get("member") or dimension.get("members") or []
    for member in members:
        if member.get("memberNameEn") == name:
            return int(member["memberId"])
    raise KeyError(f"Member not found in {dimension.get('dimensionNameEn')}: {name}")


def make_coordinate(metadata: dict[str, Any], geography: str, component: str) -> str:
    geo_dim = dimension_by_name(metadata, "Geography")
    component_dim = dimension_by_name(metadata, "Electric power, components")
    n_positions = max(int(d["dimensionPositionId"]) for d in dimensions(metadata))
    coordinate = [0] * n_positions
    coordinate[int(geo_dim["dimensionPositionId"]) - 1] = member_id(geo_dim, geography)
    coordinate[int(component_dim["dimensionPositionId"]) - 1] = member_id(component_dim, component)
    return ".".join(str(x) for x in coordinate)


def resolve_vectors(session: requests.Session, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    requested = []
    for province in PROVINCES:
        for component in COMPONENTS:
            requested.append(
                {
                    "province": province,
                    "component": component,
                    "coordinate": make_coordinate(metadata, province, component),
                }
            )

    by_coordinate = {item["coordinate"]: item for item in requested}
    resolved: list[dict[str, Any]] = []
    for batch in chunks(requested, 50):
        payload = [
            {"productId": PRODUCT_ID, "coordinate": item["coordinate"]}
            for item in batch
        ]
        responses = _post(session, "getSeriesInfoFromCubePidCoord", payload)
        for response in responses:
            obj = response.get("object") or {}
            coordinate = str(obj.get("coordinate", ""))
            source = by_coordinate.get(coordinate)
            if source is None:
                continue
            if response.get("status") != "SUCCESS" or obj.get("responseStatusCode") != 0:
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


def fetch_data(session: requests.Session, resolved: list[dict[str, Any]], latest_n: int = 132) -> pd.DataFrame:
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
                        "component": source["component"],
                        "value": point.get("value"),
                        "vector_id": int(vector_id),
                        "coordinate": source["coordinate"],
                        "status_code": point.get("statusCode"),
                        "symbol_code": point.get("symbolCode"),
                        "scalar_factor_code": point.get("scalarFactorCode"),
                        "frequency_code": point.get("frequencyCode"),
                        "release_time": point.get("releaseTime"),
                        "series_title": source.get("series_title"),
                        "member_uom_code": source.get("member_uom_code"),
                    }
                )

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No WDS data points were returned")
    df["ref_date"] = pd.to_datetime(df["ref_date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.sort_values(["province", "component", "ref_date"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2016)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/statcan_25100016_wds"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session:
        metadata = get_metadata(session)
        resolved = resolve_vectors(session, metadata)
        pd.DataFrame(resolved).to_csv(args.output_dir / "resolved_vectors.csv", index=False)

        df = fetch_data(session, resolved)
        df = df[df["ref_date"].dt.year.between(args.start_year, args.end_year)].copy()
        if df.empty:
            raise RuntimeError("No rows remained after year filtering")
        df.to_csv(args.output_dir / "statcan_25100016_wds_raw.csv", index=False)

        print(f"Resolved {len(resolved)} vectors")
        print(f"Saved {len(df):,} observations for {args.start_year}-{args.end_year}")
        print("Status-code counts:")
        print(df["status_code"].value_counts(dropna=False).sort_index().to_string())


if __name__ == "__main__":
    main()
