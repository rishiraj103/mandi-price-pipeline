"""Run a SQL file against the local Parquet model with DuckDB.

Creates `mandi.*` views over data/ so the same SQL files run here and on Athena.
Usage: python -m tools.query_local sql/checks/orphan_keys.sql [--csv out.csv]
"""
import argparse
from pathlib import Path

import duckdb

PARTITIONED = {
    "fact_price_report": "model/fact_price_report/*/*.parquet",
    "curated": "curated/*/*.parquet",
    "rejected": "rejected/*/*.parquet",
}
UNPARTITIONED = ["dim_date", "dim_market", "dim_commodity"]


def connect(base="data"):
    con = duckdb.connect()
    con.execute("CREATE SCHEMA mandi")
    for name, pattern in PARTITIONED.items():
        # arrival_date is a string partition on Athena; keep the same type here
        con.execute(f"CREATE VIEW mandi.{name} AS SELECT * FROM read_parquet('{base}/{pattern}', "
                    "hive_partitioning = true, union_by_name = true, hive_types = {'arrival_date': VARCHAR})")
    for name in UNPARTITIONED:
        con.execute(f"CREATE VIEW mandi.{name} AS SELECT * FROM read_parquet('{base}/model/{name}/*.parquet')")
    # dq files already carry arrival_date and are tiny, so read them unpartitioned
    con.execute(f"CREATE VIEW mandi.dq AS SELECT * FROM read_json_auto('{base}/dq/*/dq_summary.json')")
    return con


def main():
    p = argparse.ArgumentParser()
    p.add_argument("sql_file")
    p.add_argument("--base", default="data")
    p.add_argument("--csv")
    args = p.parse_args()
    df = connect(args.base).execute(Path(args.sql_file).read_text()).df()
    if args.csv:
        df.to_csv(args.csv, index=False)
    print(df.to_string(max_rows=60))


if __name__ == "__main__":
    main()
