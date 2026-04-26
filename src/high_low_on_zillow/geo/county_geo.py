import json
from pathlib import Path

import pandas as pd
import plotly.express as px

from high_low_on_zillow.paths import EXTERNAL_DIR


BAY_AREA_COUNTY_FIPS = {
    "Alameda": "06001",
    "Contra Costa": "06013",
    "Marin": "06041",
    "Napa": "06055",
    "San Francisco": "06075",
    "San Mateo": "06081",
    "Santa Clara": "06085",
    "Solano": "06095",
    "Sonoma": "06097",
}


def add_county_fips(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "county" in out.columns:
        county_col = "county"
    elif "geo_name" in out.columns:
        county_col = "geo_name"
    else:
        raise ValueError("Expected either 'county' or 'geo_name' column for county FIPS mapping.")

    out["fips"] = out[county_col].map(BAY_AREA_COUNTY_FIPS)
    return out


def load_county_geojson(path: Path | None = None) -> dict:
    if path is None:
        path = EXTERNAL_DIR / "geojson-counties-fips.json"

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_geojson_to_bay_area(geojson: dict) -> dict:
    bay_area_fips = set(BAY_AREA_COUNTY_FIPS.values())

    features = [
        feature
        for feature in geojson["features"]
        if str(feature.get("id")) in bay_area_fips
    ]

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def build_county_choropleth(
    kpi_df: pd.DataFrame,
    value_col: str,
    title: str,
    color_label: str,
):
    map_df = add_county_fips(kpi_df)
    map_df = map_df.dropna(subset=["fips", value_col]).copy()

    geojson = load_county_geojson()
    bay_area_geojson = filter_geojson_to_bay_area(geojson)

    fig = px.choropleth_mapbox(
        map_df,
        geojson=bay_area_geojson,
        locations="fips",
        color=value_col,
        featureidkey="id",
        hover_name="geo_name",
        hover_data={
            value_col: ":,.2f",
            "mom_pct": ":.2f",
            "yoy_pct": ":.2f",
            "fips": False,
        },
        labels={
            value_col: color_label,
            "mom_pct": "MoM %",
            "yoy_pct": "YoY %",
        },
        mapbox_style="carto-positron",
        center={"lat": 37.65, "lon": -122.1},
        zoom=7,
        opacity=0.7,
        title=title,
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=50, b=0),
        height=600,
    )

    return fig