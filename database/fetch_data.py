import requests
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import API_KEY, LOCATIONS, JSON_RAW_FILE, FORECAST_DAYS, API_URL

MAX_FETCH_WORKERS = 6
REQUEST_TIMEOUT_SEC = 20


def fetch_location(location):
    """Fetch weather for a single city."""
    url = API_URL.format(location=location)
    print(f"Fetching data for {location}...", flush=True)
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SEC)
    response.raise_for_status()
    return location, response.json()


def fetch_weather_forecast():
    """
    Fetches the forecast weather data for all configured locations from the weatherapi.com API.
    Saves the fetched JSON list locally for subsequent usage in the pipeline.
    """
    print(
        f"Fetching weather forecast from API for {len(LOCATIONS)} locations "
        f"({FORECAST_DAYS} days, parallel)...",
        flush=True,
    )
    all_data = []
    errors = []

    with ThreadPoolExecutor(max_workers=MAX_FETCH_WORKERS) as executor:
        futures = {executor.submit(fetch_location, loc): loc for loc in LOCATIONS}
        for future in as_completed(futures):
            location = futures[future]
            try:
                _, data = future.result()
                all_data.append(data)
                print(f"Done: {location}", flush=True)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching data for {location}: {e}", file=sys.stderr)
                errors.append((location, e))
            
    if not all_data:
        # Try reading local cached JSON if API fails, to be robust
        if os.path.exists(JSON_RAW_FILE):
            print(f"Attempting to read from local cache file: {JSON_RAW_FILE}")
            with open(JSON_RAW_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        if errors:
            raise errors[0][1]
        raise Exception("No data could be fetched and no cache exists.")

    # Save JSON data locally
    with open(JSON_RAW_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4)
    
    print(f"Successfully fetched and saved raw data for {len(all_data)} locations to {JSON_RAW_FILE}")
    if errors:
        print(f"Warnings: Failed to fetch data for: {[loc for loc, _ in errors]}")
    return all_data

if __name__ == "__main__":
    try:
        fetch_weather_forecast()
    except Exception as e:
        print(f"Fetch failed: {e}")
        sys.exit(1)
