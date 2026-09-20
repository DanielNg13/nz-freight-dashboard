# NZ Container Freight Flows

Analysis of New Zealand container port volumes, January 2012 – June 2026,
using Ministry of Transport Freight Information Gathering System (FIGS) data.

**→ [Read the findings](docs/INSIGHTS.md)**

## Headline

New Zealand container volumes fell 3% below their 2019 level during the
pandemic and recovered within nine months. They then fell 9.4% below 2019
by January 2024 and took two years to recover. The pandemic was not the
disruption.

## Stack

pandas → SQLite (star schema) → SQL → Power BI

## Pipeline

```
python src/02_clean.py        # raw extracts → star-schema tables
python src/03_load_sqlite.py  # → db/freight.db, with foreign key constraints
python src/04_run_queries.py  # → results/*.csv
```

Raw files in `data/raw/` are never modified. All cleaning is reproducible
in code, and the loader verifies that the database total matches the raw
source exactly before anything downstream runs.

## Data model

Star schema: `fact_container_volume` (22,474 rows, monthly grain) joined to
`dim_date`, `dim_port`, `dim_container_type` and `dim_trade`.

`dim_date` carries a `ports_reporting` count computed from the data itself.
This is what surfaces the mid-2025 break where Ports of Auckland stopped
reporting — a break that would otherwise read as a 19% demand decline.

## Analysis queries

| Query | Question |
|---|---|
| `01_annual_yoy.sql` | Annual volume and growth, with a data-completeness flag |
| `02_seasonal_index.sql` | Monthly seasonal index by port, 2012–2019 baseline |
| `03_port_share.sql` | Each port's share of national volume over time |
| `04_disruption_index.sql` | Rolling 12-month volume indexed to 2019 |
| `05_empty_imbalance.sql` | Empty container share by port and direction |

## Validation

FIGS-derived Port of Tauranga volume for FY26 is 894,761 TEU against a
published import/export figure of 924,105 TEU — a 3.2% difference,
consistent with FIGS excluding transhipment and under-capturing roughly
2% of containers annually.

## Source

Ministry of Transport, Freight Information Gathering System (FIGS) —
Containers. Extracted 18 September 2026.