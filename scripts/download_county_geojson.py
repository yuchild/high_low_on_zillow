from pathlib import Path
import requests

from high_low_on_zillow.paths import EXTERNAL_DIR


GEOJSON_URL = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"


def main() -> None:
    out_path = EXTERNAL_DIR / "geojson-counties-fips.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(GEOJSON_URL, timeout=120)
    response.raise_for_status()

    out_path.write_text(response.text, encoding="utf-8")

    print(f"Saved county GeoJSON to: {out_path}")
    print(f"File size: {out_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()