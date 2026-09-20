"""
03_load_sqlite.py - load processed star-schema tables into SQLite.

Reads:  data/processed/*.csv
Writes: db/freight.db  (rebuilt from scratch each run)

The schema declares primary and foreign keys. SQLite does not enforce
foreign keys by default, so we switch them on explicitly - that is what
makes a bad join fail here instead of silently in Power BI.
"""

import sqlite3
import pandas as pd
from pathlib import Path

PROCESSED = Path("data/processed")
DB = Path("db/freight.db")

SCHEMA = """
DROP TABLE IF EXISTS fact_container_volume;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_port;
DROP TABLE IF EXISTS dim_container_type;
DROP TABLE IF EXISTS dim_trade;

CREATE TABLE dim_date (
    date_key          INTEGER PRIMARY KEY,   -- YYYYMM
    date              TEXT    NOT NULL,      -- first day of month, ISO
    year              INTEGER NOT NULL,
    quarter           TEXT    NOT NULL,
    month_num         INTEGER NOT NULL,
    month_name        TEXT    NOT NULL,
    month_label       TEXT    NOT NULL,
    financial_year    INTEGER NOT NULL,      -- Jul-Jun, NZ port convention
    month_index       INTEGER NOT NULL,
    ports_reporting   INTEGER NOT NULL,
    is_complete_month INTEGER NOT NULL
);

CREATE TABLE dim_port (
    port_key          INTEGER PRIMARY KEY,
    port              TEXT    NOT NULL UNIQUE,
    island            TEXT    NOT NULL,
    first_month       TEXT    NOT NULL,
    last_month        TEXT    NOT NULL,
    series_ends_early INTEGER NOT NULL
);

CREATE TABLE dim_container_type (
    container_type_key INTEGER PRIMARY KEY,
    container_type     TEXT    NOT NULL UNIQUE,
    size_ft            INTEGER NOT NULL,
    is_reefer          INTEGER NOT NULL,
    teu_per_box        INTEGER NOT NULL
);

CREATE TABLE dim_trade (
    trade_key INTEGER PRIMARY KEY,
    trade     TEXT NOT NULL UNIQUE
);

CREATE TABLE fact_container_volume (
    date_key           INTEGER NOT NULL,
    port_key           INTEGER NOT NULL,
    container_type_key INTEGER NOT NULL,
    trade_key          INTEGER NOT NULL,
    load_status        TEXT    NOT NULL,   -- degenerate dimension
    teu                INTEGER NOT NULL,
    loaded_teu         INTEGER NOT NULL,
    empty_teu          INTEGER NOT NULL,
    tonnes             INTEGER NOT NULL,
    FOREIGN KEY (date_key)           REFERENCES dim_date(date_key),
    FOREIGN KEY (port_key)           REFERENCES dim_port(port_key),
    FOREIGN KEY (container_type_key) REFERENCES dim_container_type(container_type_key),
    FOREIGN KEY (trade_key)          REFERENCES dim_trade(trade_key)
);

CREATE INDEX idx_fact_date ON fact_container_volume(date_key);
CREATE INDEX idx_fact_port ON fact_container_volume(port_key);
"""


def main():
    DB.parent.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()   # rebuild from scratch - the CSVs are the source of truth

    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    con.executescript(SCHEMA)

    tables = [
        "dim_date", "dim_port", "dim_container_type",
        "dim_trade", "fact_container_volume",
    ]
    for name in tables:
        df = pd.read_csv(PROCESSED / f"{name}.csv")
        df.to_sql(name, con, if_exists="append", index=False)
        n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"loaded {name:<24} {n:>6} rows")

    # --- integrity checks ---
    print("\n--- foreign key check ---")
    violations = con.execute("PRAGMA foreign_key_check;").fetchall()
    print(f"violations: {len(violations)}" if violations else "clean")

    print("\n--- fact total vs source ---")
    total = con.execute("SELECT SUM(teu) FROM fact_container_volume").fetchone()[0]
    raw_total = pd.read_csv("data/raw/FIGS_containers.csv")["Teu"].sum()
    print(f"db:  {total:,}")
    print(f"raw: {raw_total:,}")
    print("MATCH" if total == raw_total else "MISMATCH - stop and investigate")

    print("\n--- loaded + empty reconciles to total ---")
    bad = con.execute("""
        SELECT COUNT(*) FROM fact_container_volume
        WHERE loaded_teu + empty_teu <> teu
    """).fetchone()[0]
    print(f"rows failing: {bad}")

    con.commit()
    con.close()
    print(f"\ndatabase written to {DB}")


if __name__ == "__main__":
    main()