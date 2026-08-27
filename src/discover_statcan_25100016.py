"""Discover Statistics Canada Table 25-10-0016-01 dimensions and members via WDS.

This is intentionally metadata-only. We use the returned official labels to decide
which receipts/deliveries/availability series belong in the PEI import-dependence
analysis before fetching any observations.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest"
PRODUCT_ID = 25100016


def main() -> None:
    out_dir = Path("data/raw/statcan_25100016_discovery")
    out_dir.mkdir(parents=True, exist_ok=True)

    response = requests.post(
        f"{BASE_URL}/getCubeMetadata",
        json=[{"productId": PRODUCT_ID}],
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload or payload[0].get("status") != "SUCCESS":
        raise RuntimeError(f"StatsCan metadata request failed: {payload}")

    metadata = payload[0]["object"]
    if metadata.get("responseStatusCode") != 0:
        raise RuntimeError(f"StatsCan returned non-zero response status: {metadata}")

    (out_dir / "statcan_25100016_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    rows = []
    dimensions = metadata.get("dimension") or metadata.get("dimensions") or []
    for dimension in dimensions:
        members = dimension.get("member") or dimension.get("members") or []
        for member in members:
            rows.append(
                {
                    "dimension_position": dimension.get("dimensionPositionId"),
                    "dimension_name": dimension.get("dimensionNameEn"),
                    "member_id": member.get("memberId"),
                    "member_name": member.get("memberNameEn"),
                    "unit_of_measure_code": member.get("unitOfMeasureCode"),
                    "scalar_factor_code": member.get("scalarFactorCode"),
                }
            )

    members_df = pd.DataFrame(rows)
    members_df.to_csv(out_dir / "statcan_25100016_members.csv", index=False)

    print(f"Table: {metadata.get('cubeTitleEn')}")
    print(f"Dimensions: {len(dimensions)}")
    for name, group in members_df.groupby("dimension_name", dropna=False):
        print(f"\n{name} ({len(group)} members)")
        for member_name in group["member_name"].tolist():
            print(f"- {member_name}")


if __name__ == "__main__":
    main()
