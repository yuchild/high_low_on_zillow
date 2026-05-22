from high_low_on_zillow.processing.zillow_processor import (
    process_home_prices,
    process_rentals,
    process_inventory,
    process_sales,
    process_zip_home_values,
    process_zip_forecasts,
    process_zip_rentals,
)
from high_low_on_zillow.processing.affordability import build_affordability_dataset


def main():
    print("Processing county home prices...")
    df_home = process_home_prices()
    print("Rows:", len(df_home))

    print("\nProcessing county rentals...")
    df_rent = process_rentals()
    print("Rows:", len(df_rent))

    print("\nProcessing metro inventory...")
    df_inventory = process_inventory()
    print("Rows:", len(df_inventory))

    print("\nProcessing metro sales...")
    df_sales = process_sales()
    print("Rows:", len(df_sales))

    print("\nProcessing affordability...")
    df_aff = build_affordability_dataset()
    print("Rows:", len(df_aff))

    print("\nProcessing ZIP home values...")
    df_zip_home = process_zip_home_values()
    print("Rows:", len(df_zip_home))

    print("\nProcessing ZIP forecasts...")
    df_zip_forecasts = process_zip_forecasts()
    print("Rows:", len(df_zip_forecasts))

    print("\nProcessing ZIP rentals...")
    df_zip_rentals = process_zip_rentals()
    print("Rows:", len(df_zip_rentals))

if __name__ == "__main__":
    main()