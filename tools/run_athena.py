"""Run SQL files on Athena through the `mandi` workgroup and print results and data scanned.

`BUCKET` in a file is replaced by $S3_BUCKET.
Usage: python -m tools.run_athena sql/athena_ddl/*.sql
       python -m tools.run_athena sql/analytics/q1_weekly_price_change.sql --csv docs/results/q1.csv
"""
import argparse
import os
import time
from pathlib import Path

import boto3
import pandas as pd
from dotenv import load_dotenv

WORKGROUP = "mandi"


def run(sql, athena=None):
    """Run one statement; returns (DataFrame, megabytes scanned)."""
    athena = athena or boto3.client("athena")
    qid = athena.start_query_execution(QueryString=sql, WorkGroup=WORKGROUP)["QueryExecutionId"]
    while True:
        q = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
        state = q["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)
    if state != "SUCCEEDED":
        raise RuntimeError(f"{state}: {q['Status'].get('StateChangeReason')}")

    rows, header = [], None
    for page in athena.get_paginator("get_query_results").paginate(QueryExecutionId=qid):
        for r in page["ResultSet"]["Rows"]:
            values = [c.get("VarCharValue") for c in r["Data"]]
            if header is None:
                header = values
            else:
                rows.append(values)
    scanned_mb = q["Statistics"].get("DataScannedInBytes", 0) / 1e6
    return pd.DataFrame(rows, columns=header), scanned_mb


def main():
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    p.add_argument("--csv")
    args = p.parse_args()
    load_dotenv(".env")
    for f in args.files:
        df, mb = run(Path(f).read_text().replace("BUCKET", os.environ["S3_BUCKET"]))
        print(f"== {f}  ({mb:.2f} MB scanned, {len(df)} rows)")
        if len(df):
            print(df.to_string(max_rows=40))
        if args.csv:
            df.to_csv(args.csv, index=False)


if __name__ == "__main__":
    main()
