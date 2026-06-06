import os
import sys
import pymysql
import pandas as pd
import numpy as np
from config import (
    DB_HOST,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
    DB_PORT,
    CSV_MASTER_REPORT,
    CSV_CURRENT,
    CSV_FORECAST_DAY,
    CSV_FORECAST_HOUR
)

def run_sql_schema(conn):
    """
    Reads schema.sql, splits it into separate commands,
    and runs each statement to set up the database and tables.
    """
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    print("Executing schema.sql to create database and tables...")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Clean single-line comments and empty lines first
    cleaned_lines = []
    for line in schema_sql.splitlines():
        trimmed = line.strip()
        if not trimmed.startswith("--") and not trimmed.startswith("#"):
            cleaned_lines.append(line)
    
    cleaned_schema = "\n".join(cleaned_lines)
    statements = cleaned_schema.split(";")
    
    with conn.cursor() as cursor:
        for statement in statements:
            # Clean statement
            statement = statement.strip()
            # Ignore empty statements
            if not statement:
                continue
            
            try:
                cursor.execute(statement)
            except Exception as e:
                print(f"Error executing statement:\n{statement}\nError: {e}", file=sys.stderr)
                raise e
    conn.commit()
    print("Database schema successfully applied.")

def load_csv_to_table(conn, table_name, csv_path):
    """
    Reads a CSV file and inserts all rows into the specified MySQL table.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at {csv_path}")

    df = pd.read_csv(csv_path)
    
    # Convert all NaN/NaT/Null to None so pymysql inserts them as SQL NULL
    df = df.where(pd.notnull(df), None)
    
    columns = list(df.columns)
    # Wrap column names in backticks in case they conflict with SQL reserved words
    escaped_cols = [f"`{col}`" for col in columns]
    col_str = ", ".join(escaped_cols)
    placeholders = ", ".join(["%s"] * len(columns))
    
    insert_query = f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders})"
    
    cursor = conn.cursor()
    # Convert rows to tuple list, converting all NaN/NaT/Null to None for MySQL compatibility
    records = []
    for row in df.itertuples(index=False, name=None):
        cleaned_row = tuple(None if pd.isna(val) else val for val in row)
        records.append(cleaned_row)
    
    print(f"Loading {len(records)} records from {os.path.basename(csv_path)} into table `{table_name}`...")
    cursor.executemany(insert_query, records)
    conn.commit()
    cursor.close()
    print(f"Successfully loaded data into `{table_name}`.")

def tables_exist(conn):
    with conn.cursor() as cursor:
        cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
        if not cursor.fetchone():
            return False
        cursor.execute(f"USE `{DB_NAME}`")
        cursor.execute("SHOW TABLES")
        existing = {row[0] for row in cursor.fetchall()}
    required = {"current_weather", "forecast_day", "forecast_hour", "master_report"}
    return required.issubset(existing)


def setup_and_load_database():
    """
    Connects to MySQL, ensures schema exists, and appends CSV data.
    """
    print(f"Connecting to MySQL server at {DB_HOST}:{DB_PORT} as {DB_USER}...", flush=True)
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            autocommit=True
        )
    except Exception as e:
        print(f"Failed to connect to MySQL server. Please make sure MySQL is running on {DB_HOST}:{DB_PORT} and credentials are correct.\nError: {e}", file=sys.stderr)
        raise e

    try:
        if tables_exist(conn):
            print("Tables already exist — skipping schema.sql.", flush=True)
        else:
            run_sql_schema(conn)

        conn.select_db(DB_NAME)
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE current_weather")
            cursor.execute("TRUNCATE TABLE forecast_day")
            cursor.execute("TRUNCATE TABLE forecast_hour")
            cursor.execute("TRUNCATE TABLE master_report")
        conn.commit()
        # Load CSVs
        load_csv_to_table(conn, "current_weather", CSV_CURRENT)
        load_csv_to_table(conn, "forecast_day", CSV_FORECAST_DAY)
        load_csv_to_table(conn, "forecast_hour", CSV_FORECAST_HOUR)
        load_csv_to_table(conn, "master_report", CSV_MASTER_REPORT)
        
    finally:
        conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    try:
        setup_and_load_database()
    except Exception as e:
        print(f"Database loading failed: {e}")
        sys.exit(1)
