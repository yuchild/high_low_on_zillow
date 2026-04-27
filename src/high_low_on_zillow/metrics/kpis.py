import pandas as pd
from high_low_on_zillow.paths import PROCESSED_DIR


def compute_latest_kpis(
    df: pd.DataFrame,
    value_col: str,
    output_name: str,
) -> pd.DataFrame:
    required_cols = {"date", value_col}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if "geo_name" in df.columns:
        geo_col = "geo_name"
    elif "county" in df.columns:
        geo_col = "county"
    elif "metro" in df.columns:
        geo_col = "metro"
    else:
        raise ValueError("No geography column found. Expected geo_name, county, or metro.")

    work = df.copy()
    work = work.sort_values([geo_col, "date"]).reset_index(drop=True)

    work["prev_month_value"] = work.groupby(geo_col)[value_col].shift(1)
    work["prev_year_value"] = work.groupby(geo_col)[value_col].shift(12)

    work["mom_pct"] = ((work[value_col] - work["prev_month_value"]) / work["prev_month_value"]) * 100
    work["yoy_pct"] = ((work[value_col] - work["prev_year_value"]) / work["prev_year_value"]) * 100

    latest_date = work["date"].max()
    latest = work.loc[work["date"] == latest_date].copy()

    latest = latest[
        [
            geo_col,
            "date",
            value_col,
            "prev_month_value",
            "prev_year_value",
            "mom_pct",
            "yoy_pct",
        ]
    ].copy()

    latest = latest.rename(columns={geo_col: "geo_name"})

    # compatibility for existing app code
    if geo_col == "county":
        latest["county"] = latest["geo_name"]
    elif geo_col == "metro":
        latest["metro"] = latest["geo_name"]

    latest["mom_pct"] = latest["mom_pct"].round(2)
    latest["yoy_pct"] = latest["yoy_pct"].round(2)
    latest["rank_desc"] = (
        latest[value_col]
        .rank(method="dense", ascending=False)
        .astype("Int64")
    )

    latest["rank_asc"] = (
        latest[value_col]
        .rank(method="dense", ascending=True)
        .astype("Int64")
)

    out_path = PROCESSED_DIR / output_name
    latest.to_parquet(out_path, index=False)

    return latest


def build_home_price_kpis() -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED_DIR / "bay_area_home_prices.parquet")
    return compute_latest_kpis(
        df=df,
        value_col="home_price",
        output_name="bay_area_home_price_kpis.parquet",
    )


def build_rent_kpis() -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED_DIR / "bay_area_rentals.parquet")
    return compute_latest_kpis(
        df=df,
        value_col="rent",
        output_name="bay_area_rent_kpis.parquet",
    )


def build_inventory_kpis() -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED_DIR / "bay_area_inventory_metro.parquet")
    return compute_latest_kpis(
        df=df,
        value_col="inventory",
        output_name="bay_area_inventory_kpis.parquet",
    )


def build_sales_kpis() -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED_DIR / "bay_area_sales_metro.parquet")
    return compute_latest_kpis(
        df=df,
        value_col="sales",
        output_name="bay_area_sales_kpis.parquet",
    )