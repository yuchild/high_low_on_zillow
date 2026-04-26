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
    }


def format_currency(value: float, decimals: int = 0) -> str:
    if pd.isna(value):
        return "N/A"
    return f"${value:,.{decimals}f}"


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

    return {
        "df": data["rentals"],
        "kpi_df": data["rent_kpis"],
        "value_col": "rent",
        "title": "Bay Area County Rents",
        "y_axis_title": "Rent",
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


def render_ranking_table(kpi_df: pd.DataFrame, dataset_choice: str) -> None:
    if dataset_choice == "Home Prices":
        display_df = kpi_df[
            ["geo_name", "date", "home_price", "mom_pct", "yoy_pct", "rank_desc", "rank_asc"]
        ].copy()
        display_df = display_df.rename(
            columns={
                "geo_name": "county",
                "home_price": "latest_home_price",
                "rank_desc": "highest_rank",
                "rank_asc": "lowest_rank",
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
                "rank_desc": "highest_rank",
                "rank_asc": "lowest_rank",
            }
        )

    # keep numeric but round
    display_df["mom_pct"] = display_df["mom_pct"].round(2)
    display_df["yoy_pct"] = display_df["yoy_pct"].round(2)

    st.dataframe(
        display_df.style.format({
            "mom_pct": "{:.2f}%",
            "yoy_pct": "{:.2f}%"
        }),
        use_container_width=True
    )


def render_county_map(kpi_df: pd.DataFrame, dataset_choice: str) -> None:
    if kpi_df.empty:
        st.warning("No KPI data available for the selected counties.")
        return

    base_value_col = "home_price" if dataset_choice == "Home Prices" else "rent"

    map_metric = st.selectbox(
        "Map color metric",
        options=["Latest Value", "MoM % Change", "YoY % Change"],
    )

    if map_metric == "Latest Value":
        value_col = base_value_col
        color_label = "Home Price" if dataset_choice == "Home Prices" else "Rent"
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


def main():
    st.title("🏠 High Low on Zillow")
    st.caption("Bay Area housing dashboard with county prices/rents and metro market activity")

    data = get_app_data()

    render_kpi_cards(data["home_kpis"], data["rent_kpis"])

    st.divider()
    st.subheader("Explore County Trends")

    dataset_choice = st.radio(
        "Select dataset",
        options=["Home Prices", "Rentals"],
        horizontal=True,
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
    render_county_map(
        kpi_df=kpi_df,
        dataset_choice=dataset_choice,
    )

    render_trend_chart(
        df=df,
        value_col=value_col,
        title=dataset_config["title"],
        y_axis_title=dataset_config["y_axis_title"],
    )

    st.subheader("Latest County Rankings")
    render_ranking_table(kpi_df, dataset_choice)

    st.divider()
    st.subheader("Market Activity")

    activity_choice = st.radio(
        "Select market activity dataset",
        options=["Inventory", "Sales"],
        horizontal=True,
    )

    if activity_choice == "Inventory":
        activity_df = data["inventory"].copy()
        activity_kpis = data["inventory_kpis"].copy()
        activity_value_col = "inventory"
    else:
        activity_df = data["sales"].copy()
        activity_kpis = data["sales_kpis"].copy()
        activity_value_col = "sales"

    metros = sorted(activity_df["geo_name"].dropna().unique().tolist())
    selected_metros = st.multiselect(
        "Select metros",
        options=metros,
        default=metros,
    )

    if selected_metros:
        activity_df = activity_df[activity_df["geo_name"].isin(selected_metros)].copy()
        activity_kpis = activity_kpis[activity_kpis["geo_name"].isin(selected_metros)].copy()
    else:
        st.warning("Select at least one metro.")
        return

    render_trend_chart(
        df=activity_df,
        value_col=activity_value_col,
        title=f"Bay Area Metro {activity_choice}",
        y_axis_title=activity_choice,
        color_col="geo_name",
    )

    st.dataframe(
        activity_kpis.style.format({
            "mom_pct": "{:.2f}%",
            "yoy_pct": "{:.2f}%"
        }),
        use_container_width=True,
    )


if __name__ == "__main__":
    main()