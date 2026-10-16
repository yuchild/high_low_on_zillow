
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

DATASETS = {
    "home_prices": {
        "file": "target_metros_home_prices.parquet",
        "value": "home_price",
        "output": "target_metros_home_price_kpis.parquet",
    },
    "rentals": {
        "file": "target_metros_rentals.parquet",
        "value": "rent",
        "output": "target_metros_rental_kpis.parquet",
    },
}


def build_kpis(config):
    df = pd.read_parquet(PROCESSED / config["file"])
    value_col = config["value"]

    df["date"] = pd.to_datetime(df["date"])

    # Pivot to one row per county and one column per month.
    wide = df.pivot(
        index=["metro_key", "county_fips", "county"],
        columns="date",
        values=value_col,
    )

    latest_date = df["date"].max()

    previous_date = latest_date - pd.offsets.MonthEnd(1)
    year_ago_date = latest_date - pd.offsets.MonthEnd(12)

    for date in [latest_date, previous_date, year_ago_date]:
        if date not in wide.columns:
            wide[date] = float("nan")

    result = pd.DataFrame(index=wide.index)

    result["date"] = latest_date
    result["value"] = wide[latest_date]

    result["mom_pct"] = (
        wide[latest_date] / wide[previous_date] - 1
    ) * 100

    result["yoy_pct"] = (
        wide[latest_date] / wide[year_ago_date] - 1
    ) * 100

    result = result.reset_index()

    # Rank only valid values within each metro.
    result["rank_desc"] = (
        result.groupby("metro_key")["value"]
        .rank(method="min", ascending=False)
        .astype("Int64")
    )

    result["rank_asc"] = (
        result.groupby("metro_key")["value"]
        .rank(method="min", ascending=True)
        .astype("Int64")
    )

    output_path = PROCESSED / config["output"]
    result.to_parquet(output_path, index=False)

    print(f"\n{config['output']}")
    print("Snapshot:", latest_date.date())
    print("Counties:", len(result))
    print("Valid values:", result["value"].notna().sum())
    print("Valid MoM:", result["mom_pct"].notna().sum())
    print("Valid YoY:", result["yoy_pct"].notna().sum())
    print("Saved:", output_path)


def main():
    for config in DATASETS.values():
        build_kpis(config)


if __name__ == "__main__":
    main()
