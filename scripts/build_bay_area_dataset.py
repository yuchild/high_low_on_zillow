from high_low_on_zillow.processing.zillow_processor import (
    process_home_prices,
    process_rentals,
    process_inventory,
    process_sales,
)


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


if __name__ == "__main__":
    main()