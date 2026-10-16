
from pathlib import Path

import pandas as pd

from high_low_on_zillow.paths import RAW_DIR, PROCESSED_DIR
from high_low_on_zillow.processing.zillow_processor import wide_to_long


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "geography_registry" / "metro_counties.csv"

DATASETS = {
    "home_prices": {
        "source": "County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
        "value_col": "home_price",
        "output": "target_metros_home_prices.parquet",
    },
    "rentals": {
        "source": "County_zori_uc_sfrcondomfr_sm_month.csv",
        "value_col": "rent",
        "output": "target_metros_rentals.parquet",
    },
}


def normalize_fips(series: pd.Series, width: int) -> pd.Series:
    values = series.astype("string").str.strip()
    values = values.str.replace(r"\.0$", "", regex=True)

    if not values.dropna().str.fullmatch(r"\d+").all():
        raise ValueError("Invalid FIPS values encountered.")

    return values.str.zfill(width)


def build_dataset(config: dict, registry: pd.DataFrame) -> None:
    source_path = RAW_DIR / "zillow" / config["source"]

    if not source_path.exists():
        raise FileNotFoundError(source_path)

    df = pd.read_csv(
        source_path,
        dtype={
            "StateCodeFIPS": "string",
            "MunicipalCodeFIPS": "string",
        },
        low_memory=False,
    )

    required = {
        "StateCodeFIPS",
        "MunicipalCodeFIPS",
        "RegionName",
    }
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required Zillow columns: {sorted(missing)}"
        )

    df["county_fips"] = (
        normalize_fips(df["StateCodeFIPS"], 2)
        + normalize_fips(df["MunicipalCodeFIPS"], 3)
    )

    # Keep the county's original Zillow identifiers.
    selected = df.merge(
        registry[["metro_key", "county_fips"]],
        on="county_fips",
        how="inner",
        validate="many_to_one",
    )

    matched_fips = set(selected["county_fips"].dropna())
    expected_fips = set(registry["county_fips"])

    missing_fips = sorted(expected_fips - matched_fips)

    print(f"\nDataset: {config['value_col']}")
    print(f"Zillow source counties: {len(df):,}")
    print(f"Matched county records: {len(selected):,}")
    print(f"Matched unique FIPS: {len(matched_fips)} / {len(expected_fips)}")

    if missing_fips:
        print("County FIPS without Zillow records:")
        print(", ".join(missing_fips))

    if selected.empty:
        raise ValueError("No target counties matched Zillow data.")

    # Prevent accidental duplication of county time series.
    if selected["county_fips"].duplicated().any():
        duplicates = selected.loc[
            selected["county_fips"].duplicated(keep=False),
            ["county_fips", "RegionName"],
        ]
        raise ValueError(
            f"Duplicate Zillow county records:\n{duplicates}"
        )

    long_df = wide_to_long(
        selected,
        value_name=config["value_col"],
    )

    # wide_to_long retains known Zillow metadata, but not our
    # new registry fields. Reattach them using RegionID.
    if "RegionID" not in long_df.columns:
        raise ValueError("RegionID missing from transformed data.")

    metadata = selected[
        ["RegionID", "county_fips", "metro_key"]
    ].copy()

    long_df = long_df.merge(
        metadata,
        on="RegionID",
        how="left",
        validate="many_to_one",
    )

    long_df["geo_name"] = long_df["RegionName"].astype(str)
    long_df["county"] = long_df["RegionName"].astype(str)
    long_df["geo_level"] = "county"

    long_df = long_df.sort_values(
        ["metro_key", "county_fips", "date"]
    ).reset_index(drop=True)

    output_path = PROCESSED_DIR / config["output"]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    long_df.to_parquet(output_path, index=False)

    print(f"Monthly observations: {len(long_df):,}")
    print(f"Saved: {output_path}")


def main() -> None:
    registry = pd.read_csv(
        REGISTRY_PATH,
        dtype={"county_fips": "string", "metro_key": "string"},
    )

    if registry["county_fips"].isna().any():
        raise ValueError("Registry contains missing county FIPS.")

    if not registry["county_fips"].str.fullmatch(r"\d{5}").all():
        raise ValueError("Registry contains invalid county FIPS.")

    if registry["county_fips"].duplicated().any():
        raise ValueError(
            "County FIPS belongs to more than one target metro."
        )

    print("Target metros:", registry["metro_key"].nunique())
    print("Target counties:", registry["county_fips"].nunique())

    for config in DATASETS.values():
        build_dataset(config, registry)


if __name__ == "__main__":
    main()
