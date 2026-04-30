from high_low_on_zillow.metrics.kpis import (
    build_home_price_kpis,
    build_rent_kpis,
    build_inventory_kpis,
    build_sales_kpis,
    build_affordability_kpis,
)


def main() -> None:
    print("Building home price KPI table...")
    df_home = build_home_price_kpis()
    print(df_home)

    print("\nBuilding rent KPI table...")
    df_rent = build_rent_kpis()
    print(df_rent)

    print("\nBuilding inventory KPI table...")
    df_inventory = build_inventory_kpis()
    print(df_inventory)

    print("\nBuilding sales KPI table...")
    df_sales = build_sales_kpis()
    print(df_sales)

    print("\nBuilding affordability KPI table...")
    df_aff = build_affordability_kpis()
    print(df_aff.head())


if __name__ == "__main__":
    main()