import os
from dotenv import load_dotenv

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

# Load .env file from project root
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# API Configuration
API_KEY = os.getenv("WEATHER_API_KEY")

# Fixed 14 cities — no geolocation or dynamic additions
LOCATIONS = [
    "ajmer", "bangalore", "bhopal", "chennai", "hyderabad",
    "jaipur", "kochi", "kolkata", "lucknow", "mumbai",
    "new delhi", "pune", "surat", "kota",
]

FORECAST_DAYS = 7
API_URL = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={{location}}&days={FORECAST_DAYS}&aqi=yes&alerts=no"

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "weather_report")
DB_PORT = int(os.getenv("DB_PORT", 3306))

# File Output Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_OUTPUT_DIR = os.path.join(BASE_DIR, "csv_output")
JSON_RAW_FILE = os.path.join(BASE_DIR, "weather_forecast.json")

# CSV File Paths
CSV_MASTER_REPORT = os.path.join(CSV_OUTPUT_DIR, "MasterReport.csv")
CSV_CURRENT = os.path.join(CSV_OUTPUT_DIR, "Current.csv")
CSV_FORECAST_DAY = os.path.join(CSV_OUTPUT_DIR, "ForecastDay.csv")
CSV_FORECAST_HOUR = os.path.join(CSV_OUTPUT_DIR, "ForecastHour.csv")
