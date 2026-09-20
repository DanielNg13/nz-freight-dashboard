"""
04_run_queries.py - run every query in sql/ and write results to results/.

Each .sql file produces one .csv of the same name. Those CSVs are the
only numbers allowed in the insight note - if a figure isn't in one of
them, it doesn't go in the note.
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB = Path("db/freight.db")
SQL = Path("sql")
RESULTS = Path("results")


def main():
    RESULTS.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)

    for path in sorted(SQL.glob("*.sql")):
        df = pd.read_sql(path.read_text(), con)
        out = RESULTS / f"{path.stem}.csv"
        df.to_csv(out, index=False)
        print(f"{path.name:<28} -> {out.name:<28} {len(df):>4} rows")

    con.close()


if __name__ == "__main__":
    main()