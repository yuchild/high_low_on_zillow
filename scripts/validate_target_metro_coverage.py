
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

FILES = {
    "Home Prices": (
        "target_metros_home_prices.parquet",
        "home_price",
    ),
    "Rentals": (
        "target_metros_rentals.parquet",
        "rent",
    ),
}


def main():
    datasets = {}

    for label, (filename, value_col) in FILES.items():
        df = pd.read_parquet(PROCESSED / filename)
        df["date"] = pd.to_datetime(df["date"])
        datasets[label] = df

        print(f"\n{'=' * 60}")
        print(label.upper())
        print(f"{'=' * 60}")

        print("Metros:", df["metro_key"].nunique())
        print("Counties:", df["county_fips"].nunique())
        print("Rows:", len(df))

        print(
            "Non-null observations:",
            df[value_col].notna().sum(),
        )

        print(
            "Missing value percentage:",
            round(df[value_col].isna().mean() * 100, 2),
        )

        assert not df.duplicated(
            ["county_fips", "date"]
        ).any(), "Duplicate county-month records found."

        latest_date = df["date"].max()

        latest = df[df["date"] == latest_date]

        print("Latest reporting date:", latest_date.date())
        print(
            "Counties with latest non-null data:",
            latest.loc[
                latest[value_col].notna(),
                "county_fips",
            ].nunique(),
        )

        coverage = (
            df.groupby(["metro_key", "county_fips"])
            .agg(
                first_date=("date", "min"),
                last_date=("date", "max"),
                observations=(value_col, "count"),
                total_rows=(value_col, "size"),
            )
            .reset_index()
        )

        coverage["missing_observations"] = (
            coverage["total_rows"]
            - coverage["observations"]
        )

        print("\nCounties with the most missing observations:")
        print(
            coverage.sort_values(
                "missing_observations",
                ascending=False,
            ).head(10).to_string(index=False)
        )

    home = datasets["Home Prices"]
    rent = datasets["Rentals"]

    home_counties = set(home["county_fips"])
    rent_counties = set(rent["county_fips"])

    missing_rent = home[
        home["county_fips"].isin(home_counties - rent_counties)
    ][["metro_key", "county_fips", "RegionName"]].drop_duplicates()

    print("\n" + "=" * 60)
    print("COUNTIES WITHOUT RENTAL RECORDS")
    print("=" * 60)

    if missing_rent.empty:
        print("None")
    else:
        print(
            missing_rent.sort_values(
                ["metro_key", "county_fips"]
            ).to_string(index=False)
        )


if __name__ == "__main__":
    main()
