import os
import json
import pandas as pd
from config import (
    JSON_RAW_FILE,
    CSV_OUTPUT_DIR,
    CSV_MASTER_REPORT,
    CSV_CURRENT,
    CSV_FORECAST_DAY,
    CSV_FORECAST_HOUR
)

def process_weather_data():
    """
    Reads the raw weather JSON, processes and flattens it,
    and writes 4 distinct CSV files.
    """
    if not os.path.exists(JSON_RAW_FILE):
        raise FileNotFoundError(f"Raw JSON data file {JSON_RAW_FILE} not found. Please run fetch_data.py first.")
    
    with open(JSON_RAW_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Support both single location object or list of location objects
    if isinstance(data, list):
        data_list = data
    else:
        data_list = [data]

    current_rows = []
    forecast_day_rows = []
    hour_rows = []
    master_rows = []

    for item in data_list:
        # 1. Extract Location Information
        location = item.get('location', {})
        loc_dict = {
            'location_name': location.get('name'),
            'location_region': location.get('region'),
            'location_country': location.get('country'),
            'location_lat': location.get('lat'),
            'location_lon': location.get('lon'),
            'location_tz_id': location.get('tz_id'),
            'location_localtime_epoch': location.get('localtime_epoch'),
            'location_localtime': location.get('localtime'),
        }

        # 2. Extract Current Weather Information
        current = item.get('current', {})
        current_cond = current.get('condition', {})
        current_aqi = current.get('air_quality', {})
        current_dict = {
            'current_last_updated_epoch': current.get('last_updated_epoch'),
            'current_last_updated': current.get('last_updated'),
            'current_temp_c': current.get('temp_c'),
            'current_temp_f': current.get('temp_f'),
            'current_is_day': current.get('is_day'),
            'current_condition_text': current_cond.get('text'),
            'current_condition_icon': current_cond.get('icon'),
            'current_condition_code': current_cond.get('code'),
            'current_wind_mph': current.get('wind_mph'),
            'current_wind_kph': current.get('wind_kph'),
            'current_wind_degree': current.get('wind_degree'),
            'current_wind_dir': current.get('wind_dir'),
            'current_pressure_mb': current.get('pressure_mb'),
            'current_pressure_in': current.get('pressure_in'),
            'current_precip_mm': current.get('precip_mm'),
            'current_precip_in': current.get('precip_in'),
            'current_humidity': current.get('humidity'),
            'current_cloud': current.get('cloud'),
            'current_feelslike_c': current.get('feelslike_c'),
            'current_feelslike_f': current.get('feelslike_f'),
            'current_windchill_c': current.get('windchill_c'),
            'current_windchill_f': current.get('windchill_f'),
            'current_heatindex_c': current.get('heatindex_c'),
            'current_heatindex_f': current.get('heatindex_f'),
            'current_dewpoint_c': current.get('dewpoint_c'),
            'current_dewpoint_f': current.get('dewpoint_f'),
            'current_vis_km': current.get('vis_km'),
            'current_vis_miles': current.get('vis_miles'),
            'current_uv': current.get('uv'),
            'current_gust_mph': current.get('gust_mph'),
            'current_gust_kph': current.get('gust_kph'),
            'current_will_it_rain': current.get('will_it_rain'),
            'current_chance_of_rain': current.get('chance_of_rain'),
            'current_will_it_snow': current.get('will_it_snow'),
            'current_chance_of_snow': current.get('chance_of_snow'),
            'current_short_rad': current.get('short_rad'),
            'current_diff_rad': current.get('diff_rad'),
            'current_dni': current.get('dni'),
            'current_gti': current.get('gti'),
            'current_aqi_co': current_aqi.get('co') if current_aqi else None,
            'current_aqi_no2': current_aqi.get('no2') if current_aqi else None,
            'current_aqi_o3': current_aqi.get('o3') if current_aqi else None,
            'current_aqi_so2': current_aqi.get('so2') if current_aqi else None,
            'current_aqi_pm2_5': current_aqi.get('pm2_5') if current_aqi else None,
            'current_aqi_pm10': current_aqi.get('pm10') if current_aqi else None,
            'current_aqi_us_epa_index': current_aqi.get('us-epa-index') if current_aqi else None,
            'current_aqi_gb_defra_index': current_aqi.get('gb-defra-index') if current_aqi else None,
        }

        # 3. Extract Forecast Day Information
        forecastday_list = item.get('forecast', {}).get('forecastday', [])

        # File 1 row (Location + Current) - appended once per location
        current_data = {**loc_dict, **current_dict}
        current_rows.append(current_data)

        for fday in forecastday_list:
            day_obj = fday.get('day', {})
            day_cond = day_obj.get('condition', {})
            day_aqi = day_obj.get('air_quality', {})
            astro_obj = fday.get('astro', {})
            
            fday_dict = {
                'forecast_date': fday.get('date'),
                'forecast_date_epoch': fday.get('date_epoch'),
                'day_maxtemp_c': day_obj.get('maxtemp_c'),
                'day_maxtemp_f': day_obj.get('maxtemp_f'),
                'day_mintemp_c': day_obj.get('mintemp_c'),
                'day_mintemp_f': day_obj.get('mintemp_f'),
                'day_avgtemp_c': day_obj.get('avgtemp_c'),
                'day_avgtemp_f': day_obj.get('avgtemp_f'),
                'day_maxwind_mph': day_obj.get('maxwind_mph'),
                'day_maxwind_kph': day_obj.get('maxwind_kph'),
                'day_totalprecip_mm': day_obj.get('totalprecip_mm'),
                'day_totalprecip_in': day_obj.get('totalprecip_in'),
                'day_totalsnow_cm': day_obj.get('totalsnow_cm'),
                'day_avgvis_km': day_obj.get('avgvis_km'),
                'day_avgvis_miles': day_obj.get('avgvis_miles'),
                'day_avghumidity': day_obj.get('avghumidity'),
                'day_will_it_rain': day_obj.get('daily_will_it_rain'),
                'day_chance_of_rain': day_obj.get('daily_chance_of_rain'),
                'day_will_it_snow': day_obj.get('daily_will_it_snow'),
                'day_chance_of_snow': day_obj.get('daily_chance_of_snow'),
                'day_condition_text': day_cond.get('text'),
                'day_condition_icon': day_cond.get('icon'),
                'day_condition_code': day_cond.get('code'),
                'day_uv': day_obj.get('uv'),
                'astro_sunrise': astro_obj.get('sunrise'),
                'astro_sunset': astro_obj.get('sunset'),
                'astro_moonrise': astro_obj.get('moonrise'),
                'astro_moonset': astro_obj.get('moonset'),
                'astro_moon_phase': astro_obj.get('moon_phase'),
                'astro_moon_illumination': astro_obj.get('moon_illumination'),
                'astro_is_moon_up': astro_obj.get('is_moon_up'),
                'astro_is_sun_up': astro_obj.get('is_sun_up'),
                'day_aqi_co': day_aqi.get('co') if day_aqi else None,
                'day_aqi_no2': day_aqi.get('no2') if day_aqi else None,
                'day_aqi_o3': day_aqi.get('o3') if day_aqi else None,
                'day_aqi_so2': day_aqi.get('so2') if day_aqi else None,
                'day_aqi_pm2_5': day_aqi.get('pm2_5') if day_aqi else None,
                'day_aqi_pm10': day_aqi.get('pm10') if day_aqi else None,
                'day_aqi_us_epa_index': day_aqi.get('us-epa-index') if day_aqi else None,
                'day_aqi_gb_defra_index': day_aqi.get('gb-defra-index') if day_aqi else None,
            }
            
            # File 2 row (Location + Forecast Day + Astro)
            forecast_day_data = {**loc_dict, **fday_dict}
            forecast_day_rows.append(forecast_day_data)
            
            hours_list = fday.get('hour', [])
            
            # File 3 rows (Location + Forecast Hour) and File 4 rows (Location + Current + Forecast Day + Forecast Hour)
            for hour in hours_list:
                hour_cond = hour.get('condition', {})
                hour_aqi = hour.get('air_quality', {})
                hour_dict = {
                    'hour_time_epoch': hour.get('time_epoch'),
                    'hour_time': hour.get('time'),
                    'hour_temp_c': hour.get('temp_c'),
                    'hour_temp_f': hour.get('temp_f'),
                    'hour_is_day': hour.get('is_day'),
                    'hour_condition_text': hour_cond.get('text'),
                    'hour_condition_icon': hour_cond.get('icon'),
                    'hour_condition_code': hour_cond.get('code'),
                    'hour_wind_mph': hour.get('wind_mph'),
                    'hour_wind_kph': hour.get('wind_kph'),
                    'hour_wind_degree': hour.get('wind_degree'),
                    'hour_wind_dir': hour.get('wind_dir'),
                    'hour_pressure_mb': hour.get('pressure_mb'),
                    'hour_pressure_in': hour.get('pressure_in'),
                    'hour_precip_mm': hour.get('precip_mm'),
                    'hour_precip_in': hour.get('precip_in'),
                    'hour_snow_cm': hour.get('snow_cm'),
                    'hour_humidity': hour.get('humidity'),
                    'hour_cloud': hour.get('cloud'),
                    'hour_feelslike_c': hour.get('feelslike_c'),
                    'hour_feelslike_f': hour.get('feelslike_f'),
                    'hour_windchill_c': hour.get('windchill_c'),
                    'hour_windchill_f': hour.get('windchill_f'),
                    'hour_heatindex_c': hour.get('heatindex_c'),
                    'hour_heatindex_f': hour.get('heatindex_f'),
                    'hour_dewpoint_c': hour.get('dewpoint_c'),
                    'hour_dewpoint_f': hour.get('dewpoint_f'),
                    'hour_will_it_rain': hour.get('will_it_rain'),
                    'hour_chance_of_rain': hour.get('chance_of_rain'),
                    'hour_will_it_snow': hour.get('will_it_snow'),
                    'hour_chance_of_snow': hour.get('chance_of_snow'),
                    'hour_vis_km': hour.get('vis_km'),
                    'hour_vis_miles': hour.get('vis_miles'),
                    'hour_gust_mph': hour.get('gust_mph'),
                    'hour_gust_kph': hour.get('gust_kph'),
                    'hour_uv': hour.get('uv'),
                    'hour_short_rad': hour.get('short_rad'),
                    'hour_diff_rad': hour.get('diff_rad'),
                    'hour_dni': hour.get('dni'),
                    'hour_gti': hour.get('gti'),
                    'hour_aqi_co': hour_aqi.get('co') if hour_aqi else None,
                    'hour_aqi_no2': hour_aqi.get('no2') if hour_aqi else None,
                    'hour_aqi_o3': hour_aqi.get('o3') if hour_aqi else None,
                    'hour_aqi_so2': hour_aqi.get('so2') if hour_aqi else None,
                    'hour_aqi_pm2_5': hour_aqi.get('pm2_5') if hour_aqi else None,
                    'hour_aqi_pm10': hour_aqi.get('pm10') if hour_aqi else None,
                    'hour_aqi_us_epa_index': hour_aqi.get('us-epa-index') if hour_aqi else None,
                    'hour_aqi_gb_defra_index': hour_aqi.get('gb-defra-index') if hour_aqi else None,
                }
                hour_combined = {**loc_dict, **hour_dict}
                hour_rows.append(hour_combined)
                
                # File 4: MasterReport data (Location + Current + Forecast Day + Forecast Hour)
                master_row = {**loc_dict, **current_dict, **fday_dict, **hour_combined}
                master_rows.append(master_row)

    # Ensure output directory exists
    os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

    # Save CSVs
    df_current = pd.DataFrame(current_rows)
    df_current.to_csv(CSV_CURRENT, index=False)
    print(f"Generated Current.csv at {CSV_CURRENT} ({len(current_rows)} rows)")

    df_forecast_day = pd.DataFrame(forecast_day_rows)
    df_forecast_day.to_csv(CSV_FORECAST_DAY, index=False)
    print(f"Generated ForecastDay.csv at {CSV_FORECAST_DAY} ({len(forecast_day_rows)} rows)")

    df_forecast_hour = pd.DataFrame(hour_rows)
    df_forecast_hour.to_csv(CSV_FORECAST_HOUR, index=False)
    print(f"Generated ForecastHour.csv at {CSV_FORECAST_HOUR} ({len(hour_rows)} rows)")

    df_master_report = pd.DataFrame(master_rows)
    df_master_report.to_csv(CSV_MASTER_REPORT, index=False)
    print(f"Generated MasterReport.csv at {CSV_MASTER_REPORT} ({len(master_rows)} rows)")

if __name__ == "__main__":
    process_weather_data()
