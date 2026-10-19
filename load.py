"""
load.py

Loads the Spotify charts subset into PostgreSQL, end to end:
  1. connect to the database and test the connection
  2. create the six tables (runs sql/01_create_schema.sql)
  3. read the subset CSV with pandas and land it in a stage table with to_sql
  4. move the stage data into the six normalized tables (runs sql/03_load_tables.sql)
  5. check the row counts

Before running:
  - Postgres is running and the spotify_capstone database exists
  - data/charts_subset.csv exists (run subset.py first)
  - a .env file in this folder holds your DATABASE_URL (copy .env.example)

Run it from the project folder:
    uv run load.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, types


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

# The database connection lives in .env, never in this file,
# so this script can be shared without any login details in it.
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL is missing. Copy .env.example to .env and fill it in.")
    sys.exit(1)

CSV_FILE_PATH = "data/charts_subset.csv"
STAGE_TABLE = "stage_charts"

SCHEMA_SQL = Path("sql/01_create_schema.sql")
LOAD_SQL = Path("sql/03_load_tables.sql")

TABLES = ["region", "trend", "artist", "track", "track_artist", "chart_entry"]


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: connect and test the connection
# ─────────────────────────────────────────────────────────────────────────────

def test_connection(engine):
    """Runs a tiny query so a bad connection fails here, not halfway through the load."""
    try:
        with engine.connect() as conn:
            user, db, now = conn.execute(
                text("select current_user, current_database(), now()")
            ).one()
        print(f"✅ Connected as {user} to {db} at {now}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("   Check that Postgres.app is running and the spotify_capstone database exists.")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 and 4: run a .sql file
# ─────────────────────────────────────────────────────────────────────────────

def run_sql_file(engine, path: Path):
    """Runs every statement in a .sql file inside one transaction."""
    print(f"\nRunning {path}...")
    with engine.begin() as conn:
        conn.exec_driver_sql(path.read_text())
    print(f"✅ Finished {path}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: read the CSV and land it in the stage table
# ─────────────────────────────────────────────────────────────────────────────

def load_stage(engine) -> int:
    """
    Reads the subset CSV and writes it to the stage table with to_sql.

    Every column is read and stored as text, with no type conversion.
    This follows the stage-table pattern from the course: land the raw data
    first, then convert types in SQL as a separate, visible step (step 4).
    """
    print(f"\nReading {CSV_FILE_PATH}...")
    df = pd.read_csv(CSV_FILE_PATH, dtype=str)
    print(f"Read {len(df):,} rows and {len(df.columns)} columns: {list(df.columns)}")

    print(f"Writing to {STAGE_TABLE} (all columns as text)...")
    df.to_sql(
        STAGE_TABLE,
        engine,
        if_exists="replace",
        index=False,
        dtype={col: types.Text() for col in df.columns},
        chunksize=100_000,
    )
    print(f"✅ Wrote {len(df):,} rows to {STAGE_TABLE}")
    return len(df)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: check the row counts
# ─────────────────────────────────────────────────────────────────────────────

def verify_row_counts(engine, csv_rows: int):
    """Prints the row count of every table and checks no chart rows were lost."""
    print("\nRow counts:")
    with engine.connect() as conn:
        counts = {
            table: conn.execute(text(f"select count(*) from {table}")).scalar()
            for table in TABLES
        }
    for table, count in counts.items():
        print(f"  {table:<13} {count:>10,}")

    if counts["chart_entry"] == csv_rows:
        print(f"\n✅ chart_entry matches the CSV ({csv_rows:,} rows). Load successful.")
    else:
        print(f"\n⚠️  chart_entry has {counts['chart_entry']:,} rows but the CSV has {csv_rows:,}.")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    engine = create_engine(DATABASE_URL)

    test_connection(engine)              # step 1
    run_sql_file(engine, SCHEMA_SQL)     # step 2
    csv_rows = load_stage(engine)        # step 3
    run_sql_file(engine, LOAD_SQL)       # step 4
    verify_row_counts(engine, csv_rows)  # step 5


if __name__ == "__main__":
    main()
