from pathlib import Path
import pandas as pd

from high_low_on_zillow.paths import PROCESSED_DIR, EXTERNAL_DIR


REQUIRED_FILES = [
    PROCESSED_DIR / "bay_area_home_prices.parquet",
    PROCESSED_DIR / "bay_area_rentals.parquet",
    PROCESSED_DIR / "bay_area_home_price_kpis.parquet",
    PROCESSED_DIR / "bay_area_rent_kpis.parquet",
    EXTERNAL_DIR / "geojson-counties-fips.json",
    PROCESSED_DIR / "bay_area_inventory_metro.parquet",
    PROCESSED_DIR / "bay_area_sales_metro.parquet",
    PROCESSED_DIR / "bay_area_inventory_kpis.parquet",
    PROCESSED_DIR / "bay_area_sales_kpis.parquet",
]


def validate_file_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")


def validate_parquet_schema(path: Path, required_cols: set[str]) -> None:
    df = pd.read_parquet(path)
    missing = required_cols - set(df.columns)

    if missing:
        raise ValueError(
            f"{path} is missing required columns: {sorted(missing)}. "
            f"Available columns: {df.columns.tolist()}"
        )

    if df.empty:
        raise ValueError(f"{path} is empty")


def main() -> None:
    for path in REQUIRED_FILES:
        validate_file_exists(path)

    validate_parquet_schema(
        PROCESSED_DIR / "bay_area_home_prices.parquet",
        {"county", "date", "home_price"},
    )

    validate_parquet_schema(
        PROCESSED_DIR / "bay_area_rentals.parquet",
        {"county", "date", "rent"},
    )

    validate_parquet_schema(
        PROCESSED_DIR / "bay_area_home_price_kpis.parquet",
        {"geo_name", "date", "home_price", "mom_pct", "yoy_pct", "rank_desc", "rank_asc"},
    )

    validate_parquet_schema(
        PROCESSED_DIR / "bay_area_rent_kpis.parquet",
        {"geo_name", "date", "rent", "mom_pct", "yoy_pct", "rank_desc", "rank_asc"},
    )

    validate_parquet_schema(
    PROCESSED_DIR / "bay_area_inventory_metro.parquet",
    {"geo_name", "metro", "geo_level", "date", "inventory"},
    )

    validate_parquet_schema(
        PROCESSED_DIR / "bay_area_sales_metro.parquet",
        {"geo_name", "metro", "geo_level", "date", "sales"},
    )

    validate_parquet_schema(
        PROCESSED_DIR / "bay_area_inventory_kpis.parquet",
        {"geo_name", "date", "inventory", "mom_pct", "yoy_pct", "rank_desc", "rank_asc"},
    )

    validate_parquet_schema(
        PROCESSED_DIR / "bay_area_sales_kpis.parquet",
        {"geo_name", "date", "sales", "mom_pct", "yoy_pct", "rank_desc", "rank_asc"},
    )

    print("All required data files and schemas validated successfully.")


if __name__ == "__main__":
    main()