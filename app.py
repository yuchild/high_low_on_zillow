from pathlib import Path
import sys
import re
from difflib import SequenceMatcher

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
    
import streamlit as st
import pandas as pd
import plotly.express as px
from high_low_on_zillow.geo.county_geo import build_county_choropleth
from national_visuals import render_national_map, render_national_chart, load_series


from high_low_on_zillow.utils.data_access import (
    load_home_prices,
    load_rentals,
    load_home_price_kpis,
    load_rent_kpis,
    load_inventory,
    load_sales,
    load_inventory_kpis,
    load_sales_kpis,
    load_affordability,
    load_affordability_kpis,
    load_zip_home_values,
    load_zip_rentals,
    load_zip_forecasts,
    load_zip_home_value_kpis,
    load_zip_rent_kpis,
    load_zip_forecast_kpis,
)


st.set_page_config(
    page_title="High Low on Zillow",
    page_icon="🏠",
    layout="wide",
)


@st.cache_data
def get_app_data():
    return {
        "home_prices": load_home_prices(),
        "rentals": load_rentals(),
        "home_kpis": load_home_price_kpis(),
        "rent_kpis": load_rent_kpis(),
        "inventory": load_inventory(),
        "sales": load_sales(),
        "inventory_kpis": load_inventory_kpis(),
        "sales_kpis": load_sales_kpis(),
        "affordability": load_affordability(),
        "affordability_kpis": load_affordability_kpis(),
        "zip_home_values": load_zip_home_values(),
        "zip_rentals": load_zip_rentals(),
        "zip_forecasts": load_zip_forecasts(),
        "zip_home_value_kpis": load_zip_home_value_kpis(),
        "zip_rent_kpis": load_zip_rent_kpis(),
        "zip_forecast_kpis": load_zip_forecast_kpis(),
    }


def format_percent(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    if value > 0:
        return f"{value:.2f}% ▲"
    if value < 0:
        return f"{value:.2f}% ▼"
    return f"{value:.2f}%"


def format_currency(value: float, decimals: int = 0) -> str:
    if pd.isna(value):
        return "N/A"
    return f"${value:,.{decimals}f}"


def color_percent(val):
    if pd.isna(val):
        return ""
    if val > 0:
        return "color: green"
    elif val < 0:
        return "color: red"
    return ""


def rank_badge(rank) -> str:
    if pd.isna(rank):
        return ""
    if int(rank) == 1:
        return "🥇"
    if int(rank) == 2:
        return "🥈"
    if int(rank) == 3:
        return "🥉"
    return ""


def append_rank_badges(
    name: str,
    highest_rank,
    lowest_rank=None,
    include_lowest_badge: bool = True,
) -> str:
    badges = [rank_badge(highest_rank)]

    if include_lowest_badge:
        badges.append(affordability_badge(lowest_rank))

    badge_text = " ".join(badge for badge in badges if badge)
    return f"{name} {badge_text}".strip()


def rerank_selected_geos(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    out = df.copy()

    out["ranking_1_highest"] = (
        out[value_col]
        .rank(method="dense", ascending=False)
        .astype("Int64")
    )

    out["ranking_1_lowest"] = (
        out[value_col]
        .rank(method="dense", ascending=True)
        .astype("Int64")
    )

    return out


def affordability_badge(rank) -> str:
    if pd.isna(rank):
        return ""
    if int(rank) == 1:
        return "💰"
    if int(rank) == 2:
        return "💵"
    if int(rank) == 3:
        return "🏡"
    return ""


def render_kpi_cards(home_kpis: pd.DataFrame, rent_kpis: pd.DataFrame) -> None:
    latest_home_avg = home_kpis["home_price"].mean()
    latest_rent_avg = rent_kpis["rent"].mean()

    top_home_row = home_kpis.sort_values("home_price", ascending=False).iloc[0]
    top_rent_row = rent_kpis.sort_values("rent", ascending=False).iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Avg Bay Area Home Price",
            format_currency(latest_home_avg, 0),
        )

    with col2:
        st.metric(
            "Avg Bay Area Rent",
            format_currency(latest_rent_avg, 0),
        )

    with col3:
        st.metric(
            "Highest Home Price County",
            top_home_row["geo_name"],
            delta=f"{top_home_row['yoy_pct']:.2f}% YoY",
        )

    with col4:
        st.metric(
            "Highest Rent County",
            top_rent_row["geo_name"],
            delta=f"{top_rent_row['yoy_pct']:.2f}% YoY",
        )


def get_dataset_config(data, dataset_choice: str):
    if dataset_choice == "Home Prices":
        return {
            "df": data["home_prices"],
            "kpi_df": data["home_kpis"],
            "value_col": "home_price",
            "title": "Bay Area County Home Prices",
            "y_axis_title": "Home Price",
        }

    if dataset_choice == "Rentals":
        return {
            "df": data["rentals"],
            "kpi_df": data["rent_kpis"],
            "value_col": "rent",
            "title": "Bay Area County Rents",
            "y_axis_title": "Rent",
        }

    return {
        "df": data["affordability"],
        "kpi_df": data["affordability_kpis"],
        "value_col": "price_to_rent",
        "title": "Bay Area County Price-to-Rent Ratio",
        "y_axis_title": "Price-to-Rent Ratio",
    }


def get_zip_dataset_config(data, zip_choice: str):
    if zip_choice == "Home Values":
        return {
            "df": data["zip_home_values"],
            "kpi_df": data["zip_home_value_kpis"],
            "value_col": "home_value",
            "title": "Bay Area ZIP Home Values",
            "y_axis_title": "Home Value",
            "has_trend": True,
        }

    if zip_choice == "Rentals":
        return {
            "df": data["zip_rentals"],
            "kpi_df": data["zip_rent_kpis"],
            "value_col": "rent",
            "title": "Bay Area ZIP Rents",
            "y_axis_title": "Rent",
            "has_trend": True,
        }

    return {
        "df": data["zip_forecasts"],
        "kpi_df": data["zip_forecast_kpis"],
        "value_col": "forecast_growth",
        "title": "Bay Area ZIP Forecast Growth",
        "y_axis_title": "Forecast Growth",
        "has_trend": False,
    }


def render_trend_chart(
    df: pd.DataFrame,
    value_col: str,
    title: str,
    y_axis_title: str,
    color_col: str = "county",
    focused_geo: str | None = None,
) -> None:
    if df.empty:
        st.warning("No data available for the selected date range.")
        return

    chart_df = df.sort_values([color_col, "date"]).copy()
    chart_df[value_col] = pd.to_numeric(
        chart_df[value_col], errors="coerce"
    )

    geographies = sorted(
        chart_df[color_col].dropna().unique().tolist()
    )

    if not geographies:
        st.warning("No geographic data available.")
        return

    chart_key = f"trend_{color_col}_{value_col}"

    st.markdown("#### Chart Display Options")

    # Row 1: Value transformation
    price_view = st.radio(
        "Value display",
        ["Actual Values", "Indexed Growth"],
        horizontal=True,
        key=f"{chart_key}_value_view",
    )

    # Row 2: Focus controls
    control_col1, control_col2 = st.columns([2, 1])

    with control_col1:
        display_mode = st.radio(
            "Display mode",
            ["Compare All", "Highlight", "Isolate"],
            horizontal=True,
            key=f"{chart_key}_mode",
        )

        if focused_geo == "All Counties":
            display_mode = "Compare All"
        elif focused_geo is not None:
            display_mode = "Highlight"

    with control_col2:
        if focused_geo is not None:
            focus_geo = focused_geo
        else:
            focus_geo = st.selectbox(
                "Focus geography",
                options=geographies,
                key=f"{chart_key}_focus",
                disabled=(display_mode == "Compare All"),
            )

    plot_col = value_col
    plot_y_title = y_axis_title
    plot_title = title

    if price_view == "Indexed Growth":
        # The first valid positive observation for each geography
        # within the selected date range becomes the baseline.
        chart_df["index_base"] = chart_df.groupby(
            color_col
        )[value_col].transform(
            lambda s: s.dropna().iloc[0]
            if not s.dropna().empty else float("nan")
        )

        # Avoid division by zero or invalid baselines.
        valid_base = (
            chart_df["index_base"].notna()
            & (chart_df["index_base"] > 0)
        )

        chart_df["indexed_value"] = float("nan")

        chart_df.loc[valid_base, "indexed_value"] = (
            chart_df.loc[valid_base, value_col]
            / chart_df.loc[valid_base, "index_base"]
            * 100
        )

        plot_col = "indexed_value"
        plot_y_title = "Index (Base = 100)"
        plot_title = f"{title} — Indexed Growth"

        st.caption(
            "Each geography starts at an index of 100 using its "
            "first available positive value within the selected date range. "
            "An index of 120 represents 20% growth from that baseline. "
            "Geographies may have different baseline dates."
        )

    fig = px.line(
        chart_df,
        x="date",
        y=plot_col,
        color=color_col,
        title=plot_title,
        markers=False,
    )

    for trace in fig.data:
        is_focused = str(trace.name) == str(focus_geo)

        if display_mode == "Compare All":
            trace.visible = True
            trace.line.width = 3
            trace.opacity = 1.0

        elif display_mode == "Highlight":
            trace.visible = True
            trace.line.width = 5 if is_focused else 2
            trace.opacity = 1.0 if is_focused else 0.2

        elif display_mode == "Isolate":
            trace.visible = True if is_focused else "legendonly"
            trace.line.width = 4
            trace.opacity = 1.0

        trace.mode = "lines"

        if price_view == "Indexed Growth":
            trace.hovertemplate = (
                "%{fullData.name}"
                "&lt;br&gt;Date: %{x|%b %Y}"
                "&lt;br&gt;Index: %{y:.2f}"
                "&lt;extra&gt;&lt;/extra&gt;"
            )

    if price_view == "Indexed Growth":
        fig.add_hline(
            y=100,
            line_dash="dash",
            line_color="gray",
            opacity=0.6,
            annotation_text="Baseline = 100",
        )

    fig.update_layout(
        height=750,
        dragmode="pan",
        hovermode="closest",
        hoverdistance=30,
        xaxis_title="Date",
        yaxis_title=plot_y_title,
        legend_title=color_col.replace("_", " ").title(),
        margin=dict(l=40, r=20, t=60, b=40),
        hoverlabel=dict(font_size=13),
    )

    fig.update_xaxes(
        showgrid=True,
        rangeslider_visible=False,
        fixedrange=False,
    )

    fig.update_yaxes(
        showgrid=True,
        tickformat=",.1f" if price_view == "Indexed Growth" else ",.0f",
        fixedrange=False,
        autorange=True,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"{chart_key}_plot",
        config={
            "scrollZoom": False,
            "displayModeBar": True,
            "displaylogo": False,
            "doubleClick": "reset",
            "modeBarButtonsToRemove": [
                "zoom2d",
                "select2d",
                "lasso2d",
                "autoScale2d",
            ],
        },
    )

    
def render_activity_table(kpi_df: pd.DataFrame, value_col: str, label: str) -> None:
    display_df = kpi_df[
        ["geo_name", "date", value_col, "mom_pct", "yoy_pct", "rank_desc", "rank_asc"]
    ].copy()

    display_df = display_df.rename(
        columns={
            "geo_name": "metro",
            value_col: label,
            "rank_desc": "highest_rank",
            "rank_asc": "lowest_rank",
        }
    )

    display_df["metro"] = display_df.apply(
        lambda row: append_rank_badges(
            name=row["metro"],
            highest_rank=row["highest_rank"],
            lowest_rank=row["lowest_rank"],
            include_lowest_badge=True,
        ),
        axis=1,
    )

    display_df = display_df.sort_values("highest_rank", na_position="last")

    styled_df = display_df.style.format({
        label: "{:,.0f}",
        "mom_pct": lambda x: format_percent(x),
        "yoy_pct": lambda x: format_percent(x),
    }).map(color_percent, subset=["mom_pct", "yoy_pct"])

    st.caption("Green = increase, Red = decrease (MoM / YoY)")
    st.dataframe(styled_df, use_container_width=True)


def render_ranking_table(
    kpi_df: pd.DataFrame,
    dataset_choice: str,
    focused_county: str = "All Counties",
) -> None:
    if dataset_choice == "Home Prices":
        display_df = kpi_df[
            ["geo_name", "date", "home_price", "mom_pct", "yoy_pct", "rank_desc", "rank_asc"]
        ].copy()
        display_df = display_df.rename(
            columns={
                "geo_name": "county",
                "home_price": "latest_home_price",
                "rank_desc": "ranking_1_highest",
                "rank_asc": "ranking_1_lowest",
            }
        )

    elif dataset_choice == "Affordability":
        display_df = kpi_df[
            ["geo_name", "date", "price_to_rent", "mom_pct", "yoy_pct", "rank_desc", "rank_asc"]
        ].copy()
        display_df = display_df.rename(
            columns={
                "geo_name": "county",
                "price_to_rent": "latest_price_to_rent",
                "rank_desc": "ranking_1_highest",
                "rank_asc": "ranking_1_lowest",
            }
        )

    else:
        display_df = kpi_df[
            ["geo_name", "date", "rent", "mom_pct", "yoy_pct", "rank_desc", "rank_asc"]
        ].copy()
        display_df = display_df.rename(
            columns={
                "geo_name": "county",
                "rent": "latest_rent",
                "rank_desc": "ranking_1_highest",
                "rank_asc": "ranking_1_lowest",
            }
        )

    if dataset_choice == "Affordability":
        display_df["county"] = display_df.apply(
            lambda row: (
                f"{row['county']} "
                f"{rank_badge(row['ranking_1_highest'])} "
                f"{affordability_badge(row['ranking_1_lowest'])}"
            ).strip(),
            axis=1,
        )

        st.caption(
            "Ranking interpretation:  \n"
            "ranking_1_highest = highest price-to-rent ratio (least affordable by this proxy 🥇 🥈 🥉)  \n"
            "ranking_1_lowest = lowest ratio (more affordable by this proxy 💰 💵 🏡)."
        )

    else:
        display_df["county"] = display_df.apply(
            lambda row: append_rank_badges(
                name=row["county"],
                highest_rank=row["ranking_1_highest"],
                lowest_rank=row["ranking_1_lowest"],
                include_lowest_badge=True,
            ),
            axis=1,
        )

        st.caption(
            "Ranking interpretation:  \n"
            "ranking_1_highest = 1 means this county has the highest value 🥇 🥈 🥉.  \n"
            "ranking_1_lowest = 1 means this county has the lowest value 💰 💵 🏡."
        )

    display_df["mom_pct"] = display_df["mom_pct"].round(2)
    display_df["yoy_pct"] = display_df["yoy_pct"].round(2)

    styled_df = display_df.style.format({
        "mom_pct": lambda x: format_percent(x),
        "yoy_pct": lambda x: format_percent(x),
    }).map(color_percent, subset=["mom_pct", "yoy_pct"])

    if focused_county != "All Counties":

        def highlight_focused_row(row):
            county_name = str(row["county"])

            if county_name.startswith(focused_county):
                return [
                    "background-color: rgba(59, 130, 246, 0.18)"
                ] * len(row)

            return [""] * len(row)

        styled_df = styled_df.apply(
            highlight_focused_row,
            axis=1,
        )

    st.dataframe(styled_df, use_container_width=True)


def render_zip_ranking_table(kpi_df: pd.DataFrame, value_col: str, label: str) -> None:
    cols = ["geo_name", "date", value_col, "rank_desc", "rank_asc"]

    if "mom_pct" in kpi_df.columns:
        cols.extend(["mom_pct", "yoy_pct"])

    display_df = kpi_df[cols].copy()

    display_df = display_df.rename(
        columns={
            "geo_name": "zip_code",
            value_col: label,
            "rank_desc": "ranking_1_highest",
            "rank_asc": "ranking_1_lowest",
        }
    )

    display_df = rerank_selected_geos(display_df, label)

    if label == "forecast_growth":
        display_df["zip_code"] = display_df.apply(
            lambda row: (
                f"{row['zip_code']} "
                f"{rank_badge(row['ranking_1_highest'])}"
            ).strip(),
            axis=1,
        )
    else:
        display_df["zip_code"] = display_df.apply(
            lambda row: append_rank_badges(
                name=row["zip_code"],
                highest_rank=row["ranking_1_highest"],
                lowest_rank=row["ranking_1_lowest"],
                include_lowest_badge=(label != "forecast_growth"),
            ),
            axis=1,
        )

    display_df = display_df.sort_values("ranking_1_highest", na_position="last")

    if label == "forecast_growth":
        st.markdown(
            "Ranking interpretation: ranking_1_highest = strongest projected ZIP growth 🥇 🥈 🥉.  \n"
            "ranking_1_lowest = weakest projected ZIP growth."
        )
    else:
        st.markdown(
            "Ranking interpretation: ranking_1_highest = highest value or least affordable 🥇 🥈 🥉.  \n"
            "ranking_1_lowest = lowest value or most affordable 💰 💵 🏡."
        )

    if "mom_pct" in display_df.columns:
        styled_df = display_df.style.format({
            "mom_pct": lambda x: format_percent(x),
            "yoy_pct": lambda x: format_percent(x),
        }).map(color_percent, subset=["mom_pct", "yoy_pct"])
    else:
        styled_df = display_df.style

    st.dataframe(styled_df, use_container_width=True)


def render_county_map(kpi_df: pd.DataFrame, dataset_choice: str) -> None:
    if kpi_df.empty:
        st.warning("No KPI data available for the selected counties.")
        return

    if dataset_choice == "Home Prices":
        base_value_col = "home_price"
        base_label = "Home Price"
    elif dataset_choice == "Rentals":
        base_value_col = "rent"
        base_label = "Rent"
    else:
        base_value_col = "price_to_rent"
        base_label = "Price-to-Rent Ratio"

    map_metric = st.selectbox(
        "Map color metric",
        options=["Latest Value", "MoM % Change", "YoY % Change"],
    )

    if map_metric == "Latest Value":
        value_col = base_value_col
        color_label = base_label
    elif map_metric == "MoM % Change":
        value_col = "mom_pct"
        color_label = "MoM %"
    else:
        value_col = "yoy_pct"
        color_label = "YoY %"

    title = f"Bay Area County {dataset_choice}: {map_metric}"

    fig = build_county_choropleth(
        kpi_df=kpi_df,
        value_col=value_col,
        title=title,
        color_label=color_label,
    )
    
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "displaylogo": False,
        },
    )


def render_market_kpi_cards(activity_kpis: pd.DataFrame, value_col: str, label: str) -> None:
    valid = activity_kpis.dropna(subset=[value_col]).copy()

    if valid.empty:
        st.warning(f"No latest {label.lower()} data available.")
        return

    avg_value = valid[value_col].mean()
    top_row = valid.sort_values(value_col, ascending=False).iloc[0]
    valid_yoy = valid.dropna(subset=["yoy_pct"]).copy()
    fastest_yoy = valid_yoy.sort_values("yoy_pct", ascending=False).iloc[0]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(f"Avg {label}", f"{avg_value:,.0f}")

    with col2:
        st.metric(
            f"Highest {label} Metro",
            top_row["geo_name"],
            delta=format_percent(top_row["yoy_pct"]),
        )

    with col3:
        st.metric(
            f"Fastest YoY Growth",
            fastest_yoy["geo_name"],
            delta=format_percent(fastest_yoy["yoy_pct"]),
        )



# National Metro Explorer: separate from the existing Bay Area data loaders.
NATIONAL_KPI_FILES = {
    "Home Prices": "target_metros_home_price_kpis.parquet",
    "Rentals": "target_metros_rental_kpis.parquet",
}

NATIONAL_METRO_NAMES = {
    "bay_area": "SF Bay Area", "new_york": "New York", "los_angeles": "Los Angeles",
    "chicago": "Chicago", "houston": "Houston", "phoenix": "Phoenix",
    "philadelphia": "Philadelphia", "san_antonio": "San Antonio",
    "san_diego": "San Diego", "dallas_fort_worth": "Dallas–Fort Worth",
    "jacksonville": "Jacksonville", "austin": "Austin",
    "charlotte": "Charlotte", "columbus": "Columbus",
    "indianapolis": "Indianapolis", "seattle": "Seattle",
    "denver": "Denver", "oklahoma_city": "Oklahoma City",
}


@st.cache_data
def load_national_kpis(metric: str) -> pd.DataFrame:
    path = ROOT_DIR / "data" / "processed" / NATIONAL_KPI_FILES[metric]
    df = pd.read_parquet(path)
    required = {"metro_key", "county_fips", "county", "date", "value",
                "mom_pct", "yoy_pct", "rank_desc", "rank_asc"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path.name} missing columns: {sorted(missing)}")
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data
def load_metro_registry():
    """Official ranked MSA list; never silently mix in stale hardcoded metros."""
    path = ROOT_DIR / "geography_registry" / "metros.csv"
    if not path.exists():
        st.error("Missing geography_registry/metros.csv. Run the top-100 registry builder first.")
        st.stop()
    registry = pd.read_csv(path, dtype={"metro_key": "string", "cbsa_code": "string"})
    required = {"metro_key", "metro_name", "states", "population_rank"}
    if required - set(registry.columns):
        raise ValueError(f"Metro registry missing columns: {sorted(required - set(registry.columns))}")
    registry["population_rank"] = pd.to_numeric(registry["population_rank"], errors="raise")
    if registry["metro_key"].duplicated().any():
        raise ValueError("Duplicate metro keys in metros.csv")
    return registry.sort_values("population_rank").reset_index(drop=True)


@st.cache_data
def load_county_registry():
    path = ROOT_DIR / "geography_registry" / "metro_counties.csv"
    registry = pd.read_csv(path, dtype={"metro_key": "string", "county_fips": "string"})
    required = {"metro_key", "county_fips"}
    if required - set(registry.columns):
        raise ValueError(f"County registry missing columns: {sorted(required - set(registry.columns))}")
    registry["county_fips"] = registry["county_fips"].str.zfill(5)
    if registry["county_fips"].duplicated().any():
        raise ValueError("Duplicate county assignments in metro_counties.csv")
    return registry


@st.cache_data
def load_expanded_registry():
    path = ROOT_DIR / "geography_registry" / "metro_expanded_counties.csv"
    if not path.exists():
        return None
    frame = pd.read_csv(path, dtype={"metro_key": "string", "county_fips": "string"})
    frame["county_fips"] = frame["county_fips"].str.zfill(5)
    return frame


@st.cache_data
def load_adjacent_pool(metric, history=False):
    if history:
        filename = ("adjacent_pool_target_metros_home_prices.parquet" if metric == "Home Prices"
                    else "adjacent_pool_target_metros_rentals.parquet")
    else:
        filename = ("adjacent_pool_home_price_kpis.parquet" if metric == "Home Prices"
                    else "adjacent_pool_rental_kpis.parquet")
    path = ROOT_DIR / "data" / "processed" / filename
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    frame["county_fips"] = frame["county_fips"].astype("string").str.zfill(5)
    frame["date"] = pd.to_datetime(frame["date"])
    return frame


def metro_label(row):
    return f"#{int(row.population_rank)} · {row.metro_name}, {row.states}"


def search_metro_options(registry: pd.DataFrame, query: str, limit: int = 25) -> list[str]:
    """Rank metro matches by city/name, state code/name, and typo tolerance."""
    query = query.casefold().strip()
    if not query:
        return registry["metro_key"].tolist()

    state_names = {
        "AL": "alabama", "AK": "alaska", "AZ": "arizona", "AR": "arkansas",
        "CA": "california", "CO": "colorado", "CT": "connecticut", "DE": "delaware",
        "DC": "district of columbia", "FL": "florida", "GA": "georgia", "HI": "hawaii",
        "ID": "idaho", "IL": "illinois", "IN": "indiana", "IA": "iowa",
        "KS": "kansas", "KY": "kentucky", "LA": "louisiana", "ME": "maine",
        "MD": "maryland", "MA": "massachusetts", "MI": "michigan", "MN": "minnesota",
        "MS": "mississippi", "MO": "missouri", "MT": "montana", "NE": "nebraska",
        "NV": "nevada", "NH": "new hampshire", "NJ": "new jersey", "NM": "new mexico",
        "NY": "new york", "NC": "north carolina", "ND": "north dakota", "OH": "ohio",
        "OK": "oklahoma", "OR": "oregon", "PA": "pennsylvania", "RI": "rhode island",
        "SC": "south carolina", "SD": "south dakota", "TN": "tennessee",
        "TX": "texas", "UT": "utah", "VT": "vermont", "VA": "virginia",
        "WA": "washington", "WV": "west virginia", "WI": "wisconsin", "WY": "wyoming",
    }
    scored = []
    for row in registry.itertuples(index=False):
        name = str(row.metro_name).casefold()
        cities = [part.strip() for part in name.split("-")]
        states = str(row.states).upper().split("-")
        state_tokens = [s.casefold() for s in states]
        state_full = [state_names.get(s, "") for s in states]
        terms = cities + [name] + state_tokens + state_full
        # Strongly prefer direct city/state matches, then partial words, then fuzzy matches.
        exact = any(query == term for term in terms)
        starts = any(term.startswith(query) for term in terms)
        contains = any(query in term for term in terms)
        word_start = any(word.startswith(query) for term in terms for word in re.split(r"[\s,]+", term))
        fuzzy = max((SequenceMatcher(None, query, term).ratio() for term in terms if term), default=0)
        fuzzy_word = max((SequenceMatcher(None, query, word).ratio()
                          for term in terms for word in re.split(r"[\s,]+", term) if word), default=0)
        similarity = max(fuzzy, fuzzy_word)
        if exact:
            score = 5.0
        elif starts:
            score = 4.0
        elif word_start:
            score = 3.5
        elif contains:
            score = 3.0
        elif len(query) >= 3 and similarity >= 0.67:
            score = similarity * 2.0
        else:
            continue
        scored.append((-score, int(row.population_rank), row.metro_key))
    scored.sort()
    return [key for _, _, key in scored[:limit]]


BAY_COUNTY_FIPS = {
    "Alameda": "06001", "Contra Costa": "06013", "Marin": "06041",
    "Napa": "06055", "San Francisco": "06075", "San Mateo": "06081",
    "Santa Clara": "06085", "Solano": "06095", "Sonoma": "06097",
}


def load_bay_area_unified(metric):
    """Adapt the original Bay Area county KPIs to the national explorer schema."""
    if metric == "Home Prices":
        source = load_home_price_kpis().copy()
        value_col = "home_price"
    else:
        source = load_rent_kpis().copy()
        value_col = "rent"
    source["county"] = source["geo_name"].astype(str).str.replace(
        r"\s+County$", "", regex=True).str.strip()
    source["county_fips"] = source["county"].map(BAY_COUNTY_FIPS)
    source = source.dropna(subset=["county_fips"])
    source = source.rename(columns={value_col: "value"})
    source["metro_key"] = "bay_area"
    return source[["metro_key", "county_fips", "county", "date", "value",
                   "mom_pct", "yoy_pct", "rank_desc", "rank_asc"]]


def load_bay_area_history(metric):
    if metric == "Home Prices":
        history, value_col = load_home_prices().copy(), "home_price"
    else:
        history, value_col = load_rentals().copy(), "rent"
    history["county"] = history["county"].astype(str).str.replace(
        r"\s+County$", "", regex=True).str.strip()
    history["county_fips"] = history["county"].map(BAY_COUNTY_FIPS)
    history = history.dropna(subset=["county_fips"])
    history["date"] = pd.to_datetime(history["date"])
    history["metro_key"] = "bay_area"
    return history[["metro_key", "county_fips", "date", value_col]]


def load_national_history_for_controls(metric: str, metro_key: str):
    """Load the same history used by the national chart for right-panel date controls."""
    from national_visuals import load_series
    history = load_series(metric)
    return history.loc[history["metro_key"] == metro_key].copy()


def render_national_metro_explorer() -> None:
    st.title("🏠 U.S. Housing Market Explorer")
    st.caption("100 largest U.S. metropolitan areas by 2025 population · County-level Zillow housing data")

    try:
        registry = load_metro_registry()
        county_registry = load_county_registry()
    except (OSError, ValueError, KeyError) as exc:
        st.error(f"Geographic registry unavailable: {exc}")
        return

    metro_names = dict(zip(registry["metro_key"], registry.apply(metro_label, axis=1)))
    metro_options = registry["metro_key"].tolist()
    # Older Streamlit session state may contain a former Bay Area-only option.
    if st.session_state.get("unified_metro") not in metro_options:
        st.session_state["unified_metro"] = "cbsa_41860" if "cbsa_41860" in metro_options else metro_options[0]

    # Persistent right-hand control panel; visualizations occupy the wider left pane.
    main_pane, control_pane = st.columns([3.4, 1.25], gap="large")
    with control_pane:
        st.subheader("Explore & filter")
        metro_query = st.text_input(
            "Search metro by city or state",
            placeholder="e.g. San Jose, California, Atlnta, TX",
            key="unified_metro_query",
            help="Search by city, state abbreviation, full state name, or approximate spelling.",
        )
        matching_metros = search_metro_options(registry, metro_query)
        if not matching_metros:
            st.info("No matching metros. Try a shorter city or state name.")
            # Keep the current selection so the dashboard remains usable.
            matching_metros = [st.session_state["unified_metro"]]
        if st.session_state["unified_metro"] not in matching_metros:
            st.session_state["unified_metro"] = matching_metros[0]
        metro_key = st.selectbox(
            "Metropolitan area · population rank",
            matching_metros,
            format_func=lambda k: metro_names[k],
            key="unified_metro",
        )
        if metro_query.strip():
            st.caption(f"{len(matching_metros)} matching metro(s) shown · clear search for all 100")
        geographic_scope = st.radio("Geographic coverage",
            ["Official metro", "Metro + adjacent counties"],
            key="unified_geographic_scope")
        metric = st.radio("Housing market", ["Home Prices", "Rentals"],
            format_func=lambda m: "Buying a home" if m == "Home Prices" else "Renting a home",
            key="unified_metric")
        change = st.selectbox("Map colors & county ranking",
            ["Latest Value", "MoM % Change", "YoY % Change"],
            format_func=lambda m: {"Latest Value": "Current dollar value", "MoM % Change": "Monthly change (%)",
                                   "YoY % Change": "Annual change (%)"}[m], key="unified_change")
    try:
        df = load_national_kpis(metric)
    except (FileNotFoundError, OSError, ValueError) as exc:
        st.error(f"Cannot load Zillow county data: {exc}")
        return
    df["county_fips"] = df["county_fips"].astype("string").str.zfill(5)
    df["date"] = pd.to_datetime(df["date"])
    global_latest = df["date"].max()
    metro_name = metro_names[metro_key].split(" · ", 1)[-1]
    expected = county_registry.loc[county_registry["metro_key"] == metro_key].copy()
    expanded = load_expanded_registry() if geographic_scope == "Metro + adjacent counties" else None
    if geographic_scope == "Metro + adjacent counties" and expanded is None:
        with control_pane:
            st.warning("Run scripts/build_adjacent_counties.py to enable adjacent counties.")
    if expanded is not None:
        scope = expanded.loc[expanded["metro_key"] == metro_key, ["county_fips", "coverage_type"]]
        if not scope.empty:
            expected = scope.merge(county_registry.drop(columns=["metro_key"], errors="ignore"),
                on="county_fips", how="left", validate="many_to_one")
            expected["metro_key"] = metro_key
    expected_count = len(expected)
    metro = df.loc[df["metro_key"] == metro_key].copy()
    if expanded is not None:
        pool = load_adjacent_pool(metric)
        if pool is None:
            with control_pane:
                st.warning("Run scripts/build_adjacent_zillow.py to load neighboring Zillow data.")
        else:
            missing_fips = set(expected["county_fips"]) - set(metro["county_fips"])
            other_metros = df.loc[df["county_fips"].isin(missing_fips)].copy()
            other_metros = other_metros.drop_duplicates(subset=["county_fips"], keep="first")
            other_metros["metro_key"] = metro_key
            missing_fips -= set(other_metros["county_fips"])
            extra = pool.loc[pool["county_fips"].isin(missing_fips)].copy()
            extra["metro_key"] = metro_key
            extra = pd.concat([other_metros, extra], ignore_index=True)
            # Rankings must be recalculated over the selected geographic scope.
            metro = pd.concat([metro, extra], ignore_index=True)
            metro["rank_desc"] = metro["value"].rank(method="min", ascending=False).astype("Int64")
            metro["rank_asc"] = metro["value"].rank(method="min", ascending=True).astype("Int64")
    valid_metros = df.loc[df["value"].notna(), "metro_key"].nunique()
    if metro.empty or metro["value"].notna().sum() == 0:
        with main_pane:
            st.warning(f"**{metro_name}: Zillow county-level {metric.lower()} data unavailable.** "
                   f"The official registry contains {expected_count} county equivalents for this metro, "
                   "but none match the current Zillow source. Connecticut's newer planning regions "
                   "require a validated geographic crosswalk; no estimates have been fabricated.")
        return

    snapshot = metro["date"].max()
    metro = metro.loc[metro["date"] == snapshot].copy()
    valid = metro.dropna(subset=["value"]).copy()
    valid_count = valid["county_fips"].nunique()
    coverage = 100 * valid_count / expected_count if expected_count else 0

    def avg_change(col):
        vals = pd.to_numeric(metro[col], errors="coerce").dropna()
        return f"{vals.mean():+.2f}%" if not vals.empty else "N/A"

    # The county registry is the authority for state names and disambiguation.
    metro = metro.merge(expected.drop(columns=["cbsa_code", "metro_title"], errors="ignore"),
                        on=["metro_key", "county_fips"], how="left", suffixes=("", "_registry"),
                        validate="many_to_one")
    state_abbr = {"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA",
      "Colorado":"CO","Connecticut":"CT","Delaware":"DE","District of Columbia":"DC","Florida":"FL",
      "Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA",
      "Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA",
      "Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE",
      "Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY",
      "North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR",
      "Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD",
      "Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA",
      "West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"}
    if "state_name" in metro.columns:
        metro["state_abbr"] = metro["state_name"].map(state_abbr).fillna("")
    else:
        metro["state_abbr"] = ""
    metro["county_label"] = metro["county"].astype(str).str.replace(r"\s+County$", "", regex=True).str.strip()
    metro["county_label"] = metro["county_label"] + metro["state_abbr"].map(lambda s: f", {s}" if s else "")
    if "coverage_type" in metro.columns:
        metro["county_label"] = metro["county_label"] + metro["coverage_type"].map(
            lambda t: " · adjacent" if t == "adjacent" else "")
    county_names = metro.set_index("county_fips")["county_label"].to_dict()
    options = sorted(county_names, key=lambda f: (county_names[f], f))
    with control_pane:
        st.divider()
        st.markdown("**County selection**")
        selected_fips = st.multiselect("Counties on map, chart & table",
            options, default=options, format_func=lambda f: county_names[f],
            key=f"unified_counties_{metro_key}_{metric}_{'adjacent' if expanded is not None else 'official'}")
    with main_pane:
        st.caption(f"**Data available through {global_latest:%B %Y}** · "
                   f"{valid_metros} of {len(registry)} ranked metros have {metric.lower()} observations. "
                   "MoM = change from prior month; YoY = change from the same month last year.")

        st.subheader(f"{metro_name} · {snapshot:%B %Y}")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Average county home value" if metric == "Home Prices" else "Average county monthly rent",
                  format_currency(valid["value"].mean()) if not valid.empty else "N/A")
        k2.metric("Average monthly change", avg_change("mom_pct"))
        k3.metric("Average annual change", avg_change("yoy_pct"))
        k4.metric("County data coverage", f"{valid_count} / {expected_count}", f"{coverage:.2f}% covered", delta_color="off")
        st.caption("Dollar values and changes are **unweighted county averages**, not official metro-wide Zillow indices. "
                   "Coverage uses the selected geographic scope as the denominator; rental coverage may be incomplete.")
        if valid_count < expected_count:
            st.caption(f"{expected_count - valid_count} official county equivalents have no current Zillow {metric.lower()} observation.")

        if not selected_fips:
            st.info("Select at least one county to continue.")
            return
        focused = metro.loc[metro["county_fips"].isin(selected_fips)].copy()
        focused["county"] = focused["county_label"]

        st.subheader("County housing map")
        render_national_map(focused, metric, metro_name, change,
                            view_key=f"unified_map_{metro_key}_{metric}_{geographic_scope}")
        st.caption("Scroll to zoom and drag to pan. Map colors reflect the selected dollar value or percentage change.")

    # A new horizontal row aligns historical chart controls with the chart itself.
    # Both columns start at the same vertical position, directly below the map.
    chart_pane, chart_control_pane = st.columns([3.4, 1.25], gap="large")
    with chart_control_pane:
        st.markdown("**Historical chart**")
        value_mode = st.radio("Display values", ["Actual Values", "Indexed Growth"],
            key="unified_chart_values")
        display_mode = st.radio("Compare counties", ["Compare All", "Highlight", "Isolate"],
            key="unified_chart_display")
        focus_label = None
        if display_mode != "Compare All":
            focus_options = sorted(county_names[f] for f in selected_fips)
            if focus_options:
                focus_label = st.selectbox("County to highlight or isolate", focus_options,
                    key=f"unified_chart_focus_{metro_key}_{metric}")
        try:
            chart_history = load_national_history_for_controls(metric, metro_key)
            if expanded is not None:
                pool_history = load_adjacent_pool(metric, history=True)
                if pool_history is not None:
                    pool_history = pool_history.loc[pool_history["county_fips"].isin(set(expected["county_fips"]))].copy()
                    pool_history["metro_key"] = metro_key
                    chart_history = pd.concat([chart_history, pool_history], ignore_index=True)
                from national_visuals import load_series
                all_history = load_series(metric)
                other_history = all_history.loc[
                    all_history["county_fips"].isin(set(expected["county_fips"]) - set(chart_history["county_fips"]))
                ].copy()
                other_history["metro_key"] = metro_key
                chart_history = pd.concat([chart_history, other_history], ignore_index=True)
        except (FileNotFoundError, OSError, ValueError, KeyError) as exc:
            chart_history = None
            st.caption(f"Historical date range unavailable: {exc}")
        chart_dates = None
        if chart_history is not None and not chart_history.empty:
            bounds = pd.to_datetime(chart_history["date"])
            low, high = bounds.min().date(), bounds.max().date()
            if low < high:
                chart_dates = st.slider("Historical date range", min_value=low,
                    max_value=high, value=(low, high), key=f"unified_chart_dates_{metric}")
    with chart_pane:
        st.subheader("Historical trends")
        render_national_chart(metro_key, focused, metric, metro_name, history_override=chart_history,
            chart_options={"date_range": chart_dates, "value_mode": value_mode,
                           "display_mode": display_mode, "focus": focus_label})

    # Full-width, static county table below the map and historical chart.
    st.divider()
    st.subheader("County rankings")
    st.caption(
        "Value Rank is within counties with Zillow observations in the selected geographic scope. "
        "Monthly and annual percentage changes describe index movements, "
        "not sales or transaction volumes."
    )
    sort_col = {"Latest Value": "value", "MoM % Change": "mom_pct", "YoY % Change": "yoy_pct"}[change]
    table = focused.sort_values(sort_col, ascending=False, na_position="last")[[
        "county_label", "value", "mom_pct", "yoy_pct", "rank_desc"
    ]].copy()
    table = table.rename(columns={
        "county_label": "County", "value": "Current Value",
        "mom_pct": "Monthly Change", "yoy_pct": "Annual Change",
        "rank_desc": "Value Rank"
    })
    styled_table = (
        table.style
        .format({
            "Current Value": format_currency,
            "Monthly Change": format_percent,
            "Annual Change": format_percent,
            "Value Rank": lambda x: "N/A" if pd.isna(x) else str(int(x)),
        })
        .map(color_percent, subset=["Monthly Change", "Annual Change"])
        .hide(axis="index")
    )
    # st.table renders every row as a static table: no internal scrolling or resize control.
    st.table(styled_table)


def main():
    render_national_metro_explorer()


if __name__ == "__main__":
    main()
