import pandas as pd
from high_low_on_zillow.paths import PROCESSED_DIR


def load_home_prices() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED_DIR / "bay_area_home_prices.parquet")


def load_rentals() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED_DIR / "bay_area_rentals.parquet")


def load_home_price_kpis() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED_DIR / "bay_area_home_price_kpis.parquet")


def load_rent_kpis() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED_DIR / "bay_area_rent_kpis.parquet")


def load_inventory():
    return pd.read_parquet(PROCESSED_DIR / "bay_area_inventory_metro.parquet")


def load_sales():
    return pd.read_parquet(PROCESSED_DIR / "bay_area_sales_metro.parquet")


def load_inventory_kpis():
    return pd.read_parquet(PROCESSED_DIR / "bay_area_inventory_kpis.parquet")


def load_sales_kpis():
    return pd.read_parquet(PROCESSED_DIR / "bay_area_sales_kpis.parquet")


def load_affordability():
    return pd.read_parquet(
        PROCESSED_DIR / "bay_area_affordability.parquet"
    )


def load_affordability_kpis():
    return pd.read_parquet(PROCESSED_DIR / "bay_area_affordability_kpis.parquet")