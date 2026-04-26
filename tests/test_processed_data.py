import pandas as pd

from high_low_on_zillow.paths import PROCESSED_DIR


def test_home_price_processed_file_has_expected_columns():
    df = pd.read_parquet(PROCESSED_DIR / "bay_area_home_prices.parquet")

    expected_cols = {"county", "date", "home_price"}
    assert expected_cols.issubset(df.columns)
    assert not df.empty


def test_rent_processed_file_has_expected_columns():
    df = pd.read_parquet(PROCESSED_DIR / "bay_area_rentals.parquet")

    expected_cols = {"county", "date", "rent"}
    assert expected_cols.issubset(df.columns)
    assert not df.empty


def test_kpi_files_have_nine_counties():
    home = pd.read_parquet(PROCESSED_DIR / "bay_area_home_price_kpis.parquet")
    rent = pd.read_parquet(PROCESSED_DIR / "bay_area_rent_kpis.parquet")

    assert home["geo_name"].nunique() == 9
    assert rent["geo_name"].nunique() == 9

def test_inventory_processed_file_has_expected_columns():
    df = pd.read_parquet(PROCESSED_DIR / "bay_area_inventory_metro.parquet")
    expected_cols = {"geo_name", "metro", "geo_level", "date", "inventory"}
    assert expected_cols.issubset(df.columns)
    assert not df.empty


def test_sales_processed_file_has_expected_columns():
    df = pd.read_parquet(PROCESSED_DIR / "bay_area_sales_metro.parquet")
    expected_cols = {"geo_name", "metro", "geo_level", "date", "sales"}
    assert expected_cols.issubset(df.columns)
    assert not df.empty


def test_market_activity_kpi_files_exist_and_have_geo_name():
    inventory = pd.read_parquet(PROCESSED_DIR / "bay_area_inventory_kpis.parquet")
    sales = pd.read_parquet(PROCESSED_DIR / "bay_area_sales_kpis.parquet")

    assert "geo_name" in inventory.columns
    assert "geo_name" in sales.columns
    assert not inventory.empty
    assert not sales.empty