import sys
from fetch_data import fetch_weather_forecast
from generate_csvs import process_weather_data
from load_db import setup_and_load_database
from dedupe_tables import dedupe_all_tables

def run_pipeline():
    """
    Main orchestrator for the weather data pipeline.
    """
    print("=" * 60, flush=True)
    print("STARTING WEATHER DATA BI PIPELINE", flush=True)
    print("=" * 60, flush=True)

    # Step 1: Fetch raw data from weather API
    print("\n--- STEP 1: FETCHING WEATHER DATA ---")
    try:
        fetch_weather_forecast()
    except Exception as e:
        print(f"Pipeline failed at Step 1 (Fetching Data): {e}", file=sys.stderr)
        sys.exit(1)

    # Step 2: Generate 4 CSV files (MasterReport, Current, ForecastDay, ForecastHour)
    print("\n--- STEP 2: GENERATING CSV FILES ---")
    try:
        process_weather_data()
    except Exception as e:
        print(f"Pipeline failed at Step 2 (Generating CSVs): {e}", file=sys.stderr)
        sys.exit(1)

    # Step 3: Setup database and load CSVs
    print("\n--- STEP 3: LOADING DATA INTO MYSQL ---")
    try:
        setup_and_load_database()
    except Exception as e:
        print(f"Pipeline failed at Step 3 (Loading MySQL): {e}", file=sys.stderr)
        sys.exit(1)

    # Step 4: Remove duplicate rows (Power BI-style dedupe on all columns)
    print("\n--- STEP 4: REMOVING DUPLICATE ROWS ---")
    try:
        dedupe_all_tables()
    except Exception as e:
        print(f"Pipeline failed at Step 4 (Deduplication): {e}", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_pipeline()
