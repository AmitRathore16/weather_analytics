import sys
import pymysql
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT

TABLES = ["current_weather", "forecast_day", "forecast_hour", "master_report"]


def dedupe_table(conn, table_name):
    """Remove duplicate rows (all columns) using SQL, like Power BI remove duplicates."""
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        before = cursor.fetchone()[0]

    if before == 0:
        print(f"`{table_name}` is empty — nothing to dedupe.", flush=True)
        return 0

    temp_table = f"`{table_name}_dedupe_tmp`"
    with conn.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
        cursor.execute(
            f"CREATE TABLE {temp_table} AS SELECT DISTINCT * FROM `{table_name}`"
        )
        cursor.execute(f"SELECT COUNT(*) FROM {temp_table}")
        after = cursor.fetchone()[0]
        removed = before - after

        if removed == 0:
            cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
            conn.commit()
            print(f"`{table_name}`: no duplicates ({before} rows).", flush=True)
            return 0

        cursor.execute(f"TRUNCATE TABLE `{table_name}`")
        cursor.execute(f"INSERT INTO `{table_name}` SELECT * FROM {temp_table}")
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
    conn.commit()
    print(f"`{table_name}`: {before} -> {after} rows (removed {removed} duplicates).", flush=True)
    return removed


def dedupe_all_tables():
    print("Removing duplicate rows from all tables...")
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        database=DB_NAME,
    )
    try:
        total_removed = 0
        for table in TABLES:
            total_removed += dedupe_table(conn, table)
        print(f"Deduplication complete. Total duplicate rows removed: {total_removed}.")
        return total_removed
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        dedupe_all_tables()
    except Exception as e:
        print(f"Deduplication failed: {e}", file=sys.stderr)
        sys.exit(1)
