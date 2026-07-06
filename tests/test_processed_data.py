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


def test_affordability_processed_file_has_expected_columns():
    df = pd.read_parquet(PROCESSED_DIR / "bay_area_affordability.parquet")

    expected_cols = {
        "county",
        "date",
        "home_price",
        "rent",
        "price_to_rent",
        "geo_name",
        "geo_level",
    }

    assert expected_cols.issubset(df.columns)
    assert not df.empty
    assert df["county"].nunique() == 9
    assert (df["price_to_rent"] > 0).all()


def test_affordability_kpi_file_has_expected_columns():
    df = pd.read_parquet(PROCESSED_DIR / "bay_area_affordability_kpis.parquet")

    expected_cols = {
        "geo_name",
        "date",
        "price_to_rent",
        "mom_pct",
        "yoy_pct",
        "rank_desc",
        "rank_asc",
    }

    assert expected_cols.issubset(df.columns)
    assert not df.empty
    assert df["geo_name"].nunique() == 9


def test_zip_processed_files_have_expected_columns():
    file_expectations = {
        "bay_area_zip_home_values.parquet": {"geo_name", "zip_code", "geo_level", "date", "home_value", "CountyName"},
        "bay_area_zip_rentals.parquet": {"geo_name", "zip_code", "geo_level", "date", "rent", "CountyName"},
        "bay_area_zip_forecasts.parquet": {"geo_name", "zip_code", "geo_level", "date", "forecast_growth", "CountyName"},
    }

    for filename, expected_cols in file_expectations.items():
        df = pd.read_parquet(PROCESSED_DIR / filename)

        assert expected_cols.issubset(df.columns)
        assert not df.empty
        assert (df["geo_level"] == "zip").all()


def test_zip_kpi_files_have_expected_columns():
    file_expectations = {
        "bay_area_zip_home_value_kpis.parquet": {"geo_name", "date", "home_value", "mom_pct", "yoy_pct", "rank_desc", "rank_asc"},
        "bay_area_zip_rent_kpis.parquet": {"geo_name", "date", "rent", "mom_pct", "yoy_pct", "rank_desc", "rank_asc"},
        "bay_area_zip_forecast_kpis.parquet": {"geo_name", "date", "forecast_growth", "rank_desc", "rank_asc"},
    }

    for filename, expected_cols in file_expectations.items():
        df = pd.read_parquet(PROCESSED_DIR / filename)

        assert expected_cols.issubset(df.columns)
        assert not df.empty