"""
02_clean.py - clean raw FIGS container extract into star-schema tables.

Reads:  data/raw/FIGS_containers.csv   (never modified)
Writes: data/processed/*.csv

Design notes:
  - Raw encodes loaded/empty implicitly: Full Teu == 0 means the row is
    empty containers; Full Teu == Teu means loaded. No partial rows exist
    (verified in 01_inspect.py). We make this explicit as load_status.
  - load_status is kept as a degenerate dimension (a text column on the
    fact) rather than its own table. With two values, a lookup table
    would add a join for no benefit.
  - ports_reporting is computed, not assumed. It is how the Auckland
    series break surfaces in the model.
"""

import pandas as pd
from pathlib import Path

RAW = Path("data/raw/FIGS_containers.csv")
OUT = Path("data/processed")

# Ports grouped by island - used for the port dimension.
ISLAND = {
    "Ports of Auckland": "North",
    "Port of Tauranga": "North",
    "Napier Port": "North",
    "CentrePort": "North",
    "Port Nelson": "South",
    "Lyttelton": "South",
    "PrimePort Timaru": "South",
    "Port Otago": "South",
    "South Port": "South",
}


def load_raw() -> pd.DataFrame:
    """Read the raw extract and drop the Tableau row-index column."""
    df = pd.read_csv(RAW)
    df = df.drop(columns=["Unnamed: 0"])
    df.columns = [
        "year", "quarter", "month_label", "trade",
        "container_type", "port", "teu", "full_teu", "tonnes",
    ]
    df["date"] = pd.to_datetime(df["month_label"], format="%b %Y")
    return df


def add_load_status(df: pd.DataFrame) -> pd.DataFrame:
    """Make the implicit loaded/empty encoding explicit."""
    partial = ((df["full_teu"] > 0) & (df["full_teu"] < df["teu"])).sum()
    if partial:
        raise ValueError(
            f"{partial} partially-loaded rows found. The loaded/empty "
            "assumption no longer holds - re-run 01_inspect.py."
        )

    df = df.copy()
    df["load_status"] = pd.where_true = df["full_teu"].eq(0).map(
        {True: "Empty", False: "Loaded"}
    )
    return df


def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    """One row per month, with an NZ port financial year (Jul-Jun)."""
    dates = pd.DataFrame({"date": sorted(df["date"].unique())})
    dates["date_key"] = dates["date"].dt.strftime("%Y%m").astype(int)
    dates["year"] = dates["date"].dt.year
    dates["month_num"] = dates["date"].dt.month
    dates["month_name"] = dates["date"].dt.strftime("%b")
    dates["month_label"] = dates["date"].dt.strftime("%b %Y")
    dates["quarter"] = (
        dates["year"].astype(str) + " Q" + dates["date"].dt.quarter.astype(str)
    )

    # NZ ports report July-June. FY2026 = Jul 2025 to Jun 2026.
    dates["financial_year"] = dates["year"] + (dates["month_num"] >= 7).astype(int)
    # Continuous month counter, 0 at the first month in the data.
    # Power BI time intelligence needs a gapless date table; ours is
    # monthly, so we offset by this instead.
    dates["month_index"] = (
        (dates["year"] - dates["year"].min()) * 12
        + dates["month_num"] - dates.loc[0, "month_num"]
    )
    # How many ports reported in each month - computed, not assumed.
    coverage = df.groupby("date")["port"].nunique().rename("ports_reporting")
    dates = dates.merge(coverage, on="date", how="left")

    n_ports = df["port"].nunique()
    dates["is_complete_month"] = (dates["ports_reporting"] == n_ports).astype(int)

    return dates[[
        "date_key", "date", "year", "quarter", "month_num", "month_name",
        "month_label", "financial_year", "month_index",
        "ports_reporting", "is_complete_month",
    ]]


def build_dim_port(df: pd.DataFrame) -> pd.DataFrame:
    """One row per port, with its own reporting window."""
    dim = (
        df.groupby("port")
        .agg(first_month=("date", "min"), last_month=("date", "max"))
        .reset_index()
    )
    dim["port_key"] = range(1, len(dim) + 1)
    dim["island"] = dim["port"].map(ISLAND)

    # Flag ports whose series ends before the dataset does.
    dataset_end = df["date"].max()
    dim["series_ends_early"] = (dim["last_month"] < dataset_end).astype(int)

    return dim[[
        "port_key", "port", "island",
        "first_month", "last_month", "series_ends_early",
    ]]


def build_dim_container_type(df: pd.DataFrame) -> pd.DataFrame:
    """Split '40ft reefer' into its size and refrigeration attributes."""
    dim = pd.DataFrame({"container_type": sorted(df["container_type"].unique())})
    dim["container_type_key"] = range(1, len(dim) + 1)
    dim["size_ft"] = dim["container_type"].str.extract(r"(\d+)ft").astype(int)
    dim["is_reefer"] = dim["container_type"].str.contains("reefer").astype(int)
    # A 40ft box counts as two TEU - useful for sanity checks later.
    dim["teu_per_box"] = (dim["size_ft"] / 20).astype(int)
    return dim[[
        "container_type_key", "container_type", "size_ft",
        "is_reefer", "teu_per_box",
    ]]


def build_dim_trade(df: pd.DataFrame) -> pd.DataFrame:
    dim = pd.DataFrame({"trade": sorted(df["trade"].unique())})
    dim["trade_key"] = range(1, len(dim) + 1)
    return dim[["trade_key", "trade"]]


def build_fact(df, dim_date, dim_port, dim_type, dim_trade) -> pd.DataFrame:
    """Replace text columns with foreign keys, keep the measures."""
    fact = df.merge(dim_date[["date_key", "date"]], on="date", how="left")
    fact = fact.merge(dim_port[["port_key", "port"]], on="port", how="left")
    fact = fact.merge(
        dim_type[["container_type_key", "container_type"]],
        on="container_type", how="left",
    )
    fact = fact.merge(dim_trade, on="trade", how="left")

    fact["empty_teu"] = fact["teu"] - fact["full_teu"]
    fact = fact.rename(columns={"full_teu": "loaded_teu"})

    fact = fact[[
        "date_key", "port_key", "container_type_key", "trade_key",
        "load_status", "teu", "loaded_teu", "empty_teu", "tonnes",
    ]]

    if fact.isna().any().any():
        raise ValueError("Null keys after join - a dimension is incomplete.")

    return fact.reset_index(drop=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    df = load_raw()
    df = add_load_status(df)

    dim_date = build_dim_date(df)
    dim_port = build_dim_port(df)
    dim_type = build_dim_container_type(df)
    dim_trade = build_dim_trade(df)
    fact = build_fact(df, dim_date, dim_port, dim_type, dim_trade)

    tables = {
        "dim_date": dim_date,
        "dim_port": dim_port,
        "dim_container_type": dim_type,
        "dim_trade": dim_trade,
        "fact_container_volume": fact,
    }
    for name, table in tables.items():
        table.to_csv(OUT / f"{name}.csv", index=False)
        print(f"wrote {name:<24} {len(table):>6} rows")

    # --- reconciliation and data-quality report ---
    print("\n--- incomplete months (not all ports reporting) ---")
    gaps = dim_date.loc[dim_date["is_complete_month"] == 0,
                        ["month_label", "ports_reporting"]]
    print(gaps.to_string(index=False) if len(gaps) else "none")

    print("\n--- ports whose series ends early ---")
    early = dim_port.loc[dim_port["series_ends_early"] == 1,
                         ["port", "last_month"]]
    print(early.to_string(index=False) if len(early) else "none")

    print("\n--- FY2026 TEU by port (Jul 2025 - Jun 2026) ---")
    fy = (
        fact.merge(dim_date[["date_key", "financial_year"]], on="date_key")
        .merge(dim_port[["port_key", "port"]], on="port_key")
        .query("financial_year == 2026")
        .groupby("port")["teu"].sum()
        .sort_values(ascending=False)
    )
    print(fy.to_string())
    print(f"\nTauranga FY26 from FIGS: {fy.get('Port of Tauranga', 0):,} TEU")
    print("Port of Tauranga published FY26: 1,213,494 TEU total,")
    print("of which imports + exports = 924,105 TEU (rest is transhipment).")


if __name__ == "__main__":
    main()