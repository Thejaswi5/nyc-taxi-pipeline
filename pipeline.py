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

# ── 5. MORE INSIGHTS ─────────────────────────────────────────────
con = duckdb.connect("taxi.duckdb")

print("\n--- Average fare by day of week ---")
days = con.execute("""
    SELECT DAYOFWEEK(tpep_pickup_datetime) AS day, 
           ROUND(AVG(total_amount), 2) AS avg_fare
    FROM raw.trips
    GROUP BY day
    ORDER BY avg_fare DESC
""").fetchall()
for row in days:
    day_name = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][row[0]]
    print(f"  {day_name}: ${row[1]}")

print("\n--- Average tip by payment type ---")
tips = con.execute("""
    SELECT payment_type,
           ROUND(AVG(tip_amount), 2) AS avg_tip
    FROM raw.trips
    GROUP BY payment_type
    ORDER BY avg_tip DESC
""").fetchall()
payment = {1:'Credit Card', 2:'Cash', 3:'No Charge', 4:'Dispute', 0:'Unknown'}
for row in tips:
    print(f"  {payment.get(row[0], 'Other')}: ${row[1]}")

con.close()


# ── 6. WINDOW FUNCTION ANALYSIS ──────────────────────────────────
print("\n--- Top 3 most expensive trips per location (locations with 1000+ trips) ---")
con = duckdb.connect("taxi.duckdb")

con.execute("""
    CREATE OR REPLACE TABLE transformed.top_trips_per_location AS
    WITH ranked AS (
        SELECT 
            PULocationID,
            total_amount,
            COUNT(*) OVER (PARTITION BY PULocationID) AS location_trip_count,
            RANK() OVER (PARTITION BY PULocationID ORDER BY total_amount DESC) AS trip_rank
        FROM raw.trips
    )
    SELECT PULocationID, total_amount, location_trip_count, trip_rank
    FROM ranked
    WHERE location_trip_count > 1000
    AND trip_rank <= 3
    ORDER BY PULocationID, trip_rank
""")

results = con.execute("""
    SELECT PULocationID, trip_rank, total_amount, location_trip_count 
    FROM transformed.top_trips_per_location 
    LIMIT 10
""").df()
print(results.to_string())
con.close()