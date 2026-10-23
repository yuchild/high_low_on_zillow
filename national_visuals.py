"""National metro historical charts and county choropleth for Streamlit."""
import json
import math
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
SERIES = {"Home Prices": ("target_metros_home_prices.parquet", "home_price"),
          "Rentals": ("target_metros_rentals.parquet", "rent")}

@st.cache_data
def load_series(metric):
    filename, value = SERIES[metric]
    df = pd.read_parquet(ROOT / "data/processed" / filename)
    required = {"metro_key", "county_fips", "date", value}
    if required - set(df.columns):
        raise ValueError(f"Missing columns: {sorted(required - set(df.columns))}")
    df["county_fips"] = df["county_fips"].astype("string").str.zfill(5)
    df["date"] = pd.to_datetime(df["date"])
    return df

@st.cache_data
def load_geojson():
    with (ROOT / "data/external/geojson-counties-fips.json").open() as f:
        return json.load(f)

def map_view_from_features(features):
    """Estimate a Mapbox center and zoom from GeoJSON county polygons."""
    coordinates = []

    def collect(value):
        if not isinstance(value, (list, tuple)) or not value:
            return
        if isinstance(value[0], (int, float)) and len(value) >= 2:
            lon, lat = value[:2]
            if math.isfinite(lon) and math.isfinite(lat):
                coordinates.append((float(lon), float(lat)))
        else:
            for part in value:
                collect(part)

    for feature in features:
        geometry = feature.get("geometry") or {}
        collect(geometry.get("coordinates", []))

    if not coordinates:
        raise ValueError("No valid polygon coordinates in county GeoJSON")

    min_lon = min(point[0] for point in coordinates)
    max_lon = max(point[0] for point in coordinates)
    min_lat = min(point[1] for point in coordinates)
    max_lat = max(point[1] for point in coordinates)
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2

    # Approximate zoom for a 1000x600 px map, with generous margins.
    lat_span = max(max_lat - min_lat, 0.05)
    lon_span = max(max_lon - min_lon, 0.05)
    lat_zoom = math.log2(360 * 600 / (256 * lat_span))
    lon_zoom = math.log2(360 * 1000 / (256 * lon_span))
    zoom = max(1.0, min(13.0, min(lat_zoom, lon_zoom) - 0.8))
    return {"lat": center_lat, "lon": center_lon}, zoom


def render_national_map(selected, metric, metro_name, map_metric):
    col = {"Latest Value": "value", "MoM % Change": "mom_pct",
           "YoY % Change": "yoy_pct"}[map_metric]
    try:
        geo = load_geojson()
    except (OSError, ValueError) as exc:
        st.warning(f"Map unavailable: {exc}")
        return
    selected = selected.copy()
    selected["county_fips"] = selected["county_fips"].astype("string").str.zfill(5)
    fips = set(selected["county_fips"].dropna())
    features = [f for f in geo["features"] if str(f.get("id", "")).zfill(5) in fips]
    present = {str(f.get("id", "")).zfill(5) for f in features}
    if not features:
        st.warning("No matching county boundaries in GeoJSON.")
        return
    if fips - present:
        st.warning(f"Missing boundaries for {len(fips - present)} counties.")
    map_df = selected[selected["county_fips"].isin(present)].copy()
    map_df["map_value"] = pd.to_numeric(map_df[col], errors="coerce")
    map_df["label"] = map_df["county"].astype(str)
    valid = map_df.dropna(subset=["map_value"])
    if valid.empty:
        st.info("No values available for this map measure.")
        return
    # Prefer MapLibre-based choropleth_map; fall back for older Plotly releases.
    use_maplibre = hasattr(px, "choropleth_map")
    choropleth = px.choropleth_map if use_maplibre else px.choropleth_mapbox
    style_arg = "map_style" if use_maplibre else "mapbox_style"
    # Preformat tooltip strings before passing them to Plotly. This avoids
    # raw float precision leaking through Plotly/Streamlit hover rendering.
    for column in ("value", "mom_pct", "yoy_pct"):
        valid.loc[:, column] = pd.to_numeric(valid[column], errors="coerce")

    def display_money(v):
        return f"${v:,.0f}" if pd.notna(v) else "N/A"

    def display_change(v):
        return f"{v:+.2f}%" if pd.notna(v) else "N/A"

    valid = valid.copy()
    valid["tooltip_value"] = valid["value"].map(display_money)
    valid["tooltip_mom"] = valid["mom_pct"].map(display_change)
    valid["tooltip_yoy"] = valid["yoy_pct"].map(display_change)
    fig = choropleth(valid,
        geojson={"type": "FeatureCollection", "features": features},
        locations="county_fips", featureidkey="id", color="map_value",
        hover_name="label", labels={"map_value": map_metric},
        custom_data=["label", "tooltip_value", "tooltip_mom", "tooltip_yoy"],
        **{style_arg: "open-street-map"}, opacity=0.75,
        title=f"{metro_name} — {metric}: {map_metric}")
    unit_label = "Typical home value" if metric == "Home Prices" else "Typical monthly rent"
    fig.update_traces(hovertemplate=(
        "<b>%{customdata[0]}</b>"
        f"<br>{unit_label}: %{{customdata[1]}}"
        "<br>Monthly change: %{customdata[2]}"
        "<br>Annual change: %{customdata[3]}"
        "<extra></extra>"
    ))
    try:
        center, zoom = map_view_from_features(features)
    except ValueError as exc:
        st.warning(f"Invalid map boundaries: {exc}")
        return
    fig.update_layout(**{("map" if use_maplibre else "mapbox"): dict(center=center, zoom=zoom)}, height=780,
                      margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig, use_container_width=True, key="unified_map",
        config={"scrollZoom": True, "displayModeBar": True, "displaylogo": False})
    if map_df["map_value"].isna().any():
        st.caption(f"{map_df['map_value'].isna().sum()} counties have no value for this measure.")


def render_national_chart(metro_key, selected, metric, metro_name, history_override=None):
    try:
        history = history_override if history_override is not None else load_series(metric)
    except (OSError, ValueError) as exc:
        st.warning(f"Historical series unavailable: {exc}")
        return
    history = history.loc[history["metro_key"] == metro_key].copy()
    selected = selected.copy()
    selected["county_fips"] = selected["county_fips"].astype("string").str.zfill(5)
    chosen = set(selected["county_fips"].dropna())
    chart = history.loc[history["county_fips"].isin(chosen)].copy()
    if chart.empty:
        st.info("No historical observations for selected counties.")
        return
    names = selected.set_index("county_fips")["county"].astype(str).to_dict()
    chart["county_label"] = chart["county_fips"].map(lambda f: names.get(f, f))
    _, value_col = SERIES[metric]
    min_date, max_date = chart["date"].min().date(), chart["date"].max().date()
    start, end = st.slider("Historical date range", min_value=min_date, max_value=max_date,
        value=(min_date, max_date), key="unified_chart_dates")
    chart = chart[chart["date"].dt.date.between(start, end)].copy()
    chart[value_col] = pd.to_numeric(chart[value_col], errors="coerce")
    chart = chart.dropna(subset=[value_col])
    if chart.empty:
        st.info("No observations in this date range.")
        return
    left, right = st.columns([1, 2])
    with left:
        value_mode = st.radio("Display values", ["Actual Values", "Indexed Growth"],
            horizontal=True, key="unified_chart_values")
    with right:
        display_mode = st.radio("Compare counties", ["Compare All", "Highlight", "Isolate"],
            horizontal=True, key="unified_chart_display")
    focus = None
    if display_mode != "Compare All":
        focus_options = sorted(chart["county_label"].dropna().unique().tolist())
        focus = st.selectbox("County to highlight or isolate", focus_options,
            key=f"unified_chart_focus_{metro_key}_{metric}")
    y = value_col
    if value_mode == "Indexed Growth":
        chart = chart.sort_values(["county_fips", "date"])
        base = chart.groupby("county_fips")[value_col].transform("first")
        chart["index"] = 100 * chart[value_col] / base.where(base > 0)
        y = "index"
        st.caption("Index = 100 at each county's first valid observation within the selected range.")
    fig = px.line(chart, x="date", y=y, color="county_label",
        title=f"{metro_name} — {metric} history",
        labels={y:"Index (base 100)" if y == "index" else "USD", "county_label":"County"})
    for trace in fig.data:
        is_focus = trace.name == focus
        if display_mode == "Highlight":
            trace.line.width = 5 if is_focus else 2
            trace.opacity = 1 if is_focus else 0.18
        elif display_mode == "Isolate":
            trace.visible = True if is_focus else "legendonly"
            trace.line.width = 4
        else:
            trace.line.width = 3
    # Plotly's default hover can expose full floating-point precision.
    if value_mode == "Indexed Growth":
        fig.update_traces(hovertemplate=(
            "<b>%{fullData.name}</b><br>%{x|%b %Y}<br>Index: %{y:.2f}"
            "<extra></extra>"
        ))
        fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
    else:
        fig.update_traces(hovertemplate=(
            "<b>%{fullData.name}</b><br>%{x|%b %Y}<br>Value: $%{y:,.0f}"
            "<extra></extra>"
        ))
    fig.update_layout(height=750, hovermode="closest", dragmode="pan",
        margin=dict(l=40, r=20, t=60, b=40))
    st.plotly_chart(fig, use_container_width=True, key="unified_chart",
        config={"displayModeBar": True, "displaylogo": False, "doubleClick": "reset"})
