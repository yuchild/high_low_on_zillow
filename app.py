from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
    
import streamlit as st
import pandas as pd
import plotly.express as px
from high_low_on_zillow.geo.county_geo import build_county_choropleth


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
) -> None:
    if df.empty:
        st.warning("No data available for the selected geography and date range.")
        return

    fig = px.line(
        df,
        x="date",
        y=value_col,
        color=color_col,
        title=title,
        markers=False,
    )

    fig.update_traces(mode="lines")

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=y_axis_title,
        legend_title=color_col.replace("_", " ").title(),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)


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
        lambda row: (
            f"{row['metro']} "
            f"{rank_badge(row['highest_rank'])} "
            f"{affordability_badge(row['lowest_rank'])}"
        ).strip(),
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


def render_ranking_table(kpi_df: pd.DataFrame, dataset_choice: str) -> None:
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
            lambda row: (
                f"{row['county']} "
                f"{rank_badge(row['ranking_1_highest'])} "
                f"{affordability_badge(row['ranking_1_lowest'])}"
            ).strip(),
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
            lambda row: (
                f"{row['zip_code']} "
                f"{rank_badge(row['ranking_1_highest'])} "
                f"{affordability_badge(row['ranking_1_lowest'])}"
            ).strip(),
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

    st.plotly_chart(fig, use_container_width=True)


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


def main():
    st.title("🏠 High Low on Zillow")
    st.caption("Bay Area housing dashboard with county prices/rents and metro market activity")

    data = get_app_data()

    render_kpi_cards(data["home_kpis"], data["rent_kpis"])

    latest_home_date = data["home_kpis"]["date"].max().date()
    latest_rent_date = data["rent_kpis"]["date"].max().date()

    st.caption(
        f"Top KPI cards use latest Zillow county snapshots: "
        f"home prices through {latest_home_date}, rents through {latest_rent_date}."
    )

    tab_prices, tab_market, tab_zip = st.tabs([
        "County Prices & Rents",
        "Metro Market Activity",
        "ZIP Code Detail",
    ])

    ## County Price and Rents
    with tab_prices:   
        st.subheader("Explore County Trends")

        dataset_choice = st.radio(
            "Select dataset",
            options=["Home Prices", "Rentals", "Affordability"],
            horizontal=True,
            key="county_dataset",
        )

        if dataset_choice == "Affordability":
            st.info(
                "Affordability uses a price-to-rent ratio: home price divided by annual rent. "
                "Higher values suggest buying is more expensive relative to renting."
            )

        dataset_config = get_dataset_config(data, dataset_choice)
        df = dataset_config["df"].copy()
        kpi_df = dataset_config["kpi_df"].copy()
        value_col = dataset_config["value_col"]

        available_counties = sorted(df["county"].dropna().unique().tolist())
        selected_counties = st.multiselect(
            "Select counties",
            options=available_counties,
            default=available_counties,
            key="county_selector",
        )

        if not selected_counties:
            st.warning("Select at least one county to display the dashboard.")
            return

        df = df[df["county"].isin(selected_counties)].copy()
        kpi_df = kpi_df[kpi_df["geo_name"].isin(selected_counties)].copy()

        min_date = df["date"].min().date()
        max_date = df["date"].max().date()

        date_range = st.slider(
            "Select date range",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            key="county_date_range",
        )

        start_date, end_date = date_range
        df = df[
            (df["date"].dt.date >= start_date) &
            (df["date"].dt.date <= end_date)
        ].copy()

        if df.empty:
            st.warning("No data available for the selected date range.")
            return

        st.subheader("County Heat Map")
        render_county_map(kpi_df=kpi_df, dataset_choice=dataset_choice)

        render_trend_chart(
            df=df,
            value_col=value_col,
            title=dataset_config["title"],
            y_axis_title=dataset_config["y_axis_title"],
        )

        st.subheader("Latest County Rankings")
        render_ranking_table(kpi_df, dataset_choice)

    ## Metro Market Activity
    with tab_market:
        st.subheader("Market Activity")

        activity_choice = st.radio(
            "Select market activity dataset",
            options=["Inventory", "Sales"],
            horizontal=True,
            key="activity_dataset",
        )

        if activity_choice == "Inventory":
            activity_df = data["inventory"].copy()
            activity_kpis = data["inventory_kpis"].copy()
            activity_value_col = "inventory"
        else:
            activity_df = data["sales"].copy()
            activity_kpis = data["sales_kpis"].copy()
            activity_value_col = "sales"

        latest_activity_date = activity_kpis["date"].max().date()

        st.caption(
            f"Market KPI cards and rankings use the latest available "
            f"{activity_choice.lower()} snapshot: {latest_activity_date}. "
            f"The date slider controls the trend chart only."
        )

        metros = sorted(activity_df["geo_name"].dropna().unique().tolist())
        selected_metros = st.multiselect(
            "Select metros",
            options=metros,
            default=metros,
            key="metro_selector",
        )

        if not selected_metros:
            st.warning("Select at least one metro.")
            return

        activity_df = activity_df[activity_df["geo_name"].isin(selected_metros)].copy()
        activity_kpis = activity_kpis[
            activity_kpis["geo_name"].isin(selected_metros)
        ].copy()

        min_activity_date = activity_df["date"].min().date()
        max_activity_date = activity_df["date"].max().date()

        activity_date_range = st.slider(
            "Select market activity date range",
            min_value=min_activity_date,
            max_value=max_activity_date,
            value=(min_activity_date, max_activity_date),
            key="activity_date_range",
        )

        activity_start_date, activity_end_date = activity_date_range

        activity_df = activity_df[
            (activity_df["date"].dt.date >= activity_start_date) &
            (activity_df["date"].dt.date <= activity_end_date)
        ].copy()

        if activity_df.empty:
            st.warning("No market activity data available for the selected date range.")
            return

        render_market_kpi_cards(
            activity_kpis=activity_kpis,
            value_col=activity_value_col,
            label=activity_choice,
        )

        render_trend_chart(
            df=activity_df,
            value_col=activity_value_col,
            title=f"Bay Area Metro {activity_choice}: {activity_start_date} to {activity_end_date}",
            y_axis_title=activity_choice,
            color_col="geo_name",
        )

        if activity_kpis[activity_value_col].isna().any():
            st.info(
                "Some metros do not have a latest value for this metric. "
                "They are shown at the bottom of the table."
            )

        render_activity_table(
            kpi_df=activity_kpis,
            value_col=activity_value_col,
            label=activity_choice.lower(),
        )
    
    ## Zip Code Detail
    with tab_zip:
        st.subheader("ZIP Code Detail")

        zip_choice = st.radio(
            "Select ZIP metric",
            options=["Home Values", "Rentals", "Forecast Growth"],
            horizontal=True,
            key="zip_metric",
        )

        zip_config = get_zip_dataset_config(data, zip_choice)
        zip_df = zip_config["df"].copy()
        zip_kpis = zip_config["kpi_df"].copy()
        zip_value_col = zip_config["value_col"]

        st.caption(
            "ZIP coverage varies by Zillow dataset. Some ZIP codes may appear for home values "
            "but not for rentals or forecasts."
        )

        counties = sorted(zip_df["CountyName"].dropna().unique().tolist())
        selected_zip_counties = st.multiselect(
            "Filter by county",
            options=counties,
            default=counties,
            key="zip_county_filter",
        )

        if not selected_zip_counties:
            st.warning("Select at least one county.")
            return

        # Filter the source ZIP-level time series by selected counties.
        zip_df = zip_df[zip_df["CountyName"].isin(selected_zip_counties)].copy()

        # Restrict KPI rows to only ZIPs that exist in the selected counties
        # for the selected metric.
        valid_county_zips = (
            zip_df["zip_code"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        zip_kpis = zip_kpis[
            zip_kpis["geo_name"].astype(str).isin(valid_county_zips)
        ].copy()

        zip_codes = sorted(valid_county_zips)
        default_zips = zip_codes[:10]

        selected_zips = st.multiselect(
            "Select ZIP codes",
            options=zip_codes,
            default=default_zips,
            key="zip_selector",
        )

        if not selected_zips:
            st.warning("Select at least one ZIP code.")
            return

        # Final ZIP selection filter.
        zip_df = zip_df[
            zip_df["zip_code"].astype(str).isin(selected_zips)
        ].copy()

        zip_kpis = zip_kpis[
            zip_kpis["geo_name"].astype(str).isin(selected_zips)
        ].copy()

        if zip_config["has_trend"]:
            min_zip_date = zip_df["date"].min().date()
            max_zip_date = zip_df["date"].max().date()

            zip_date_range = st.slider(
                "Select ZIP date range",
                min_value=min_zip_date,
                max_value=max_zip_date,
                value=(min_zip_date, max_zip_date),
                key="zip_date_range",
            )

            zip_start_date, zip_end_date = zip_date_range

            zip_df = zip_df[
                (zip_df["date"].dt.date >= zip_start_date) &
                (zip_df["date"].dt.date <= zip_end_date)
            ].copy()

            if zip_df.empty:
                st.warning("No ZIP data available for the selected date range.")
                return

            render_trend_chart(
                df=zip_df,
                value_col=zip_value_col,
                title=f"{zip_config['title']}: {zip_start_date} to {zip_end_date}",
                y_axis_title=zip_config["y_axis_title"],
                color_col="zip_code",
            )
        else:
            st.info(
                "Forecast growth is a forward-looking snapshot. "
                "It is shown as a ranking table rather than a historical trend."
            )

        st.subheader("Latest ZIP Rankings")
        render_zip_ranking_table(
            kpi_df=zip_kpis,
            value_col=zip_value_col,
            label=zip_choice.lower().replace(" ", "_"),
        )


if __name__ == "__main__":
    main()