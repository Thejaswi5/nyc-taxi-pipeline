# NYC Taxi Pipeline

An end-to-end ELT pipeline analyzing 2.9 million real NYC taxi trips from January 2024.

## What it does
- Extracts real taxi trip data from NYC TLC open data
- Loads raw data into DuckDB (local data warehouse)
- Transforms it with SQL using CTEs, aggregations, and window functions
- Answers 6 real business questions from the data

## How to run it
pip3 install duckdb requests pandas
python3 pipeline.py

## Tech stack
- Python — extraction, loading, orchestration
- DuckDB — local data warehouse
- SQL — CTEs, GROUP BY, HAVING, window functions (RANK, AVG OVER)

## Findings

### 1. Best hour for taxi drivers
5am is the most profitable hour ($37.54 avg fare) — early airport runs dominate.
5pm rush hour has 4x more trips but ranks only 8th in profitability.

### 2. Best day of the week
Monday generates the highest average fare ($28.22).
Saturday is the cheapest day ($24.73) — short leisure trips vs business travel.

### 3. Payment type vs tipping behavior
Credit card riders tip $4.17 on average.
Cash riders tip almost nothing ($0.002).
Human behavior changes based on friction.

### 4. Trip duration vs fare
Trips longer than the average duration (15.6 min) cost 67% more ($44.74 vs $26.80).
Proved using a CTE to calculate average duration and filter against it.

### 5. Zero tip rate
23.96% of all trips receive zero tip — nearly 1 in 4 rides.
Combined with finding 3, this is almost entirely explained by cash payments.

### 6. Data quality issues found
Trips recorded with distances of 312,722 miles — physically impossible.
NYC yellow cabs fit 4 passengers maximum, yet 59 trips recorded 7-9 passengers.
Real datasets are messy. A pipeline is only as trustworthy as its validation layer.

### 7. Top fares by location (window functions)
Used RANK() OVER (PARTITION BY location) to find the top 3 most expensive
trips at each pickup location — without losing any rows.
Location 33 had two trips both charging exactly $801.00 — flagged as 
either a fixed-rate route or duplicate data requiring investigation.

## SQL concepts used
- SELECT, FROM, WHERE, LIMIT
- GROUP BY, HAVING, ORDER BY
- COUNT, AVG, SUM, ROUND
- DATEDIFF, DAYOFWEEK, HOUR
- CTEs (WITH ... AS)
- Window functions: RANK() OVER, AVG() OVER, COUNT() OVER
- PARTITION BY, FILTER (WHERE ...)