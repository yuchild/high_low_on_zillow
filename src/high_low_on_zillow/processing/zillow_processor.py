from pathlib import Path
import pandas as pd
from high_low_on_zillow.config import get_settings
from high_low_on_zillow.paths import RAW_DIR, PROCESSED_DIR


def load_zillow_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def filter_bay_area_counties(df: pd.DataFrame) -> pd.DataFrame:
    settings = get_settings()
    target_counties = set(settings["bay_area_counties"])

    if "CountyName" in df.columns:
        out = df[df["CountyName"].isin(target_counties)].copy()
        if len(out) > 0:
            return out

    if "RegionName" in df.columns:
        region = df["RegionName"].astype(str).str.replace(" County", "", regex=False)
        region = region.str.replace(", CA", "", regex=False).str.strip()
        out = df[region.isin(target_counties)].copy()
        if len(out) > 0:
            return out

    if "County" in df.columns:
        county = df["County"].astype(str).str.replace(" County", "", regex=False).str.strip()
        out = df[county.isin(target_counties)].copy()
        if len(out) > 0:
            return out

    return df.iloc[0:0].copy()


def filter_bay_area_metros(df: pd.DataFrame) -> pd.DataFrame:
    settings = get_settings()
    metros = settings["bay_area_metros"]

    if "RegionName" in df.columns:
        return df[df["RegionName"].isin(metros)].copy()

    return df.iloc[0:0].copy()


def wide_to_long(df: pd.DataFrame, value_name: str) -> pd.DataFrame:
    metadata_cols = [
        "RegionID",
        "SizeRank",
        "RegionName",
        "RegionType",
        "StateName",
        "State",
        "City",
        "Metro",
        "CountyName",
        "County",
        "StateCodeFIPS",
        "MunicipalCodeFIPS",
    ]

    id_cols = [col for col in metadata_cols if col in df.columns]

    date_cols = []
    for col in df.columns:
        if col in id_cols:
            continue
        try:
            pd.to_datetime(col, format="%Y-%m-%d")
            date_cols.append(col)
        except (ValueError, TypeError):
            pass

    df_long = df.melt(
        id_vars=id_cols,
        value_vars=date_cols,
        var_name="date",
        value_name=value_name,
    )

    df_long["date"] = pd.to_datetime(df_long["date"], format="%Y-%m-%d")
    return df_long


def process_zillow_file(
    filename: str,
    value_name: str,
    output_filename: str,
    geo_level: str,
    verbose: bool = True,
) -> pd.DataFrame:
    path = RAW_DIR / "zillow" / filename

    df = load_zillow_csv(path)
    raw_rows = len(df)

    if geo_level == "county":
        df = filter_bay_area_counties(df)
    elif geo_level == "metro":
        df = filter_bay_area_metros(df)
    else:
        raise ValueError(f"Unsupported geo_level: {geo_level}")

    filtered_rows = len(df)
    df = wide_to_long(df, value_name)

    if geo_level == "county":
        df["geo_name"] = df["RegionName"].str.replace(" County", "", regex=False).str.strip()
        df["county"] = df["geo_name"]
    else:
        df["geo_name"] = df["RegionName"].str.strip()
        df["metro"] = df["geo_name"]

    df["geo_level"] = geo_level
    df = df.sort_values(["geo_name", "date"]).reset_index(drop=True)

    out_path = PROCESSED_DIR / output_filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)

    if verbose:
        print(
            f"Processed {value_name}: "
            f"geo_level={geo_level}, raw_rows={raw_rows}, "
            f"filtered_rows={filtered_rows}, output_rows={len(df)}"
        )

    return df


def process_home_prices(verbose: bool = True) -> pd.DataFrame:
    return process_zillow_file(
        filename="County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
        value_name="home_price",
        output_filename="bay_area_home_prices.parquet",
        geo_level="county",
        verbose=verbose,
    )


def process_rentals(verbose: bool = True) -> pd.DataFrame:
    return process_zillow_file(
        filename="County_zori_uc_sfrcondomfr_sm_month.csv",
        value_name="rent",
        output_filename="bay_area_rentals.parquet",
        geo_level="county",
        verbose=verbose,
    )


def process_inventory(verbose: bool = True) -> pd.DataFrame:
    return process_zillow_file(
        filename="Metro_invt_fs_uc_sfrcondo_sm_month.csv",
        value_name="inventory",
        output_filename="bay_area_inventory_metro.parquet",
        geo_level="metro",
        verbose=verbose,
    )


def process_sales(verbose: bool = True) -> pd.DataFrame:
    return process_zillow_file(
        filename="Metro_sales_count_now_uc_sfrcondo_month.csv",
        value_name="sales",
        output_filename="bay_area_sales_metro.parquet",
        geo_level="metro",
        verbose=verbose,
    )