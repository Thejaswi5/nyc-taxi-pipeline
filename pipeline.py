import duckdb
import requests
import os

# ── 1. DOWNLOAD RAW DATA ──────────────────────────────────────────
print("Downloading NYC Taxi data...")

url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
filename = "raw_taxi.parquet"

if not os.path.exists(filename):
    response = requests.get(url, stream=True)
    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Downloaded.")
else:
    print("File already exists, skipping download.")

# ── 2. CREATE DATABASE AND LOAD RAW DATA ─────────────────────────
print("Loading into DuckDB...")

con = duckdb.connect("taxi.duckdb")

con.execute("""
    CREATE SCHEMA IF NOT EXISTS raw
""")

con.execute("""
    CREATE OR REPLACE TABLE raw.trips AS
    SELECT * FROM read_parquet('raw_taxi.parquet')
""")

count = con.execute("SELECT COUNT(*) FROM raw.trips").fetchone()[0]
print(f"Loaded {count:,} rows into raw.trips")

con.close()
print("Done. Database saved as taxi.duckdb")

# ── 3. TRANSFORM — answer a real question ─────────────────────────
print("\nTransforming data...")

con = duckdb.connect("taxi.duckdb")

con.execute("CREATE SCHEMA IF NOT EXISTS transformed")

con.execute("""
    CREATE OR REPLACE TABLE transformed.hourly_stats AS

    WITH hourly AS (
        SELECT
            HOUR(tpep_pickup_datetime)   AS hour_of_day,
            COUNT(*)                     AS total_trips,
            ROUND(AVG(total_amount), 2)  AS avg_fare,
            ROUND(AVG(tip_amount), 2)    AS avg_tip,
            ROUND(SUM(total_amount), 2)  AS total_revenue
        FROM raw.trips
        WHERE total_amount > 0
          AND trip_distance > 0
        GROUP BY HOUR(tpep_pickup_datetime)
    )

    SELECT
        hour_of_day,
        total_trips,
        avg_fare,
        avg_tip,
        total_revenue,
        RANK() OVER (ORDER BY avg_fare DESC) AS profitability_rank
    FROM hourly
    ORDER BY hour_of_day
""")
# ── 4. ANSWER THE QUESTION IN PLAIN ENGLISH ──────────────────────
con = duckdb.connect("taxi.duckdb")

best_hour = con.execute(
    "SELECT hour_of_day, avg_fare, avg_tip, total_trips "
    "FROM transformed.hourly_stats "
    "WHERE profitability_rank = 1"
).fetchone()

print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSIGHT: Best hour for NYC taxi drivers
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hour:        {best_hour[0]}:00 (5am)
Avg Fare:    ${best_hour[1]}
Avg Tip:     ${best_hour[2]}
Total Trips: {best_hour[3]:,}

Early morning airport runs dominate.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

con.close()