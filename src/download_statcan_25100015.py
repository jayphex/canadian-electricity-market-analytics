"""Download Statistics Canada Table 25-10-0015-01.

The script uses Statistics Canada's Web Data Service to resolve the current
full-table CSV URL, then downloads the ZIP into data/raw/ without modifying it.
"""

from pathlib import Path
import requests

PID = "25100015"
WDS_URL = (
    "https://www150.statcan.gc.ca/t1/wds/rest/"
    f"getFullTableDownloadCSV/{PID}/en"
)
OUTPUT = Path("data/raw/25100015-eng.zip")


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    metadata_response = requests.get(WDS_URL, timeout=60)
    metadata_response.raise_for_status()
    payload = metadata_response.json()

    if payload.get("status") != "SUCCESS":
        raise RuntimeError(f"StatsCan WDS request failed: {payload}")

    download_url = payload["object"]
    data_response = requests.get(download_url, timeout=180)
    data_response.raise_for_status()
    OUTPUT.write_bytes(data_response.content)

    print(f"Downloaded {download_url}")
    print(f"Saved to {OUTPUT}")


if __name__ == "__main__":
    main()
