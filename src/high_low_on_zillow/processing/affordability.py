import pandas as pd

from high_low_on_zillow.utils.data_access import (
    load_home_prices,
    load_rentals,
)
from high_low_on_zillow.paths import PROCESSED_DIR


def build_affordability_dataset() -> pd.DataFrame:
    home = load_home_prices().copy()
    rent = load_rentals().copy()

    # merge on county + date
    df = pd.merge(
        home,
        rent,
        on=["county", "date"],
        how="inner",
    )

    # compute price-to-rent ratio
    df["price_to_rent"] = df["home_price"] / (df["rent"] * 12)

    # drop bad rows
    df = df.dropna(subset=["price_to_rent"]).copy()

    df = df[
        [
            "county",
            "date",
            "home_price",
            "rent",
            "price_to_rent",
        ]
    ].copy()

    df["geo_name"] = df["county"]
    df["geo_level"] = "county"

    output_path = PROCESSED_DIR / "bay_area_affordability.parquet"
    df.to_parquet(output_path, index=False)

    print(f"Saved affordability dataset → {output_path}")
    return df