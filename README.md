# Spotify Charts Capstone

A PostgreSQL database of daily Spotify Top 200 chart data for 15 regions in 2019 and 2020.

## Dataset

- **Source:** [Spotify Charts on Kaggle](https://www.kaggle.com/datasets/dhruvildave/spotify-charts) (`charts.csv`, about 26 million rows)
- **Subset used:** Top 200 chart, ranks 1 to 100, 2019-01-01 to 2020-12-31
- **Regions (15):** Global, United States, United Kingdom, Canada, Australia, Brazil, Mexico, Argentina, Germany, France, Spain, Italy, Netherlands, Sweden, Japan
- **Rows:** 1,096,342

The data files are not stored in this repo because they are too large for GitHub. Follow the setup steps to rebuild them.

## Schema

Six tables in third normal form. See [docs/erd.md](docs/erd.md) for the diagram.

| Table | Rows | Holds |
|---|---|---|
| region | 15 | Chart regions |
| trend | 4 | Chart movement labels |
| track | 15,667 | Songs |
| artist | 4,296 | Individual artists |
| track_artist | 21,891 | Which artists are on which songs |
| chart_entry | 1,096,342 | One song, in one region, on one day |

## Documents

- [ERD](docs/erd.md)
- [3NF proof](docs/3nf_proof.md)
- [Data dictionary](docs/data_dictionary.md)
- [Data quality (DQA) report](docs/dqa_report.md)
- ERD model for Oracle SQL Developer Data Modeler: `erd_model/ERDDesignSpotifyCaps.dmd`

## Setup

You need [uv](https://docs.astral.sh/uv/) and [Postgres.app](https://postgresapp.com/) (PostgreSQL 18).

1. Download `charts.csv` from Kaggle and put it in a `data` folder in this project.
2. Build the subset:
   ```
   uv sync
   uv run subset.py
   ```
   This should print `1096342 rows in the subset`.
3. Copy `.env.example` to `.env` and fill in your own `DATABASE_URL`. Never post or commit `.env`.
4. Create the database, then load everything with the Python loading script. Run these from the project folder:
   ```
   createdb spotify_capstone
   uv run load.py
   ```
   `load.py` creates the six tables, loads the CSV into a stage table with pandas, fills the six tables, and prints the row counts.
5. Run the data quality checks:
   ```
   psql -d spotify_capstone -f sql/04_dqa_checks.sql
   ```

## Files

| File | What it does |
|---|---|
| `explore.py` | Previews the raw file and lists every region |
| `subset.py` | Cuts the raw file down to our subset |
| `load.py` | Python loading script: runs the DDL, loads the CSV with read_csv + to_sql, fills the six tables, checks row counts |
| `sql/01_create_schema.sql` | Creates the six tables (DDL) |
| `sql/02_load_stage.sql` | Same stage load as `load.py`, written in plain SQL (backup option) |
| `sql/03_load_tables.sql` | Moves the stage data into the six tables |
| `sql/04_dqa_checks.sql` | Data quality checks used in the DQA report |
