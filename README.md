# NYC Taxi Pipeline

An end-to-end ELT pipeline analyzing 3 million real NYC taxi trips.

## What it does
- Extracts real taxi trip data from NYC open data
- Loads raw data into DuckDB (local data warehouse)
- Transforms it with SQL using CTEs and window functions
- Answers a real business question: **which hours are most profitable for drivers?**

## Key finding
5am is the most profitable hour ($37.54 avg fare) — driven by airport runs.
Midnight has 4x more trips but 25% lower fares.

## Tech stack
- Python — data extraction and pipeline orchestration
- DuckDB — local data warehouse
- SQL — CTEs, aggregations, window functions (RANK OVER)

## How to run it
pip3 install duckdb requests pandas
python3 pipeline.py

## Output
Hour:        5:00 (5am)
Avg Fare:    $37.54
Avg Tip:     $3.96
Total Trips: 17,505
Early morning airport runs dominate.
