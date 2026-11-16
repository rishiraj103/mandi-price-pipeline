"""Raw JSON for one date -> curated Parquet, rejected Parquet and a data-quality summary.

Usage: python -m transform.clean_day 2026-11-20
"""
import json
import sys
from datetime import date

import pandas as pd
import yaml

from transform import storage
from transform.rules import PRICE_COLS, RENAME, apply_rules, standardise

CURATED_COLS = ["state", "district", "market", "commodity", "commodity_code", "variety", "grade",
                *PRICE_COLS, "is_outlier"]


def load_config(path="config/commodities.yml"):
    with open(path) as f:
        return yaml.safe_load(f)["commodities"]


def clean(records, day, commodities):
    """Pure function: list of raw API records -> (curated_df, rejected_df, dq_summary)."""
    df = standardise(pd.DataFrame(records, columns=list(RENAME)),
                     {api: c["name"] for api, c in commodities.items()})
    curated, rejected = apply_rules(df, day)
    curated = curated[CURATED_COLS].astype({"commodity_code": "int32"}).reset_index(drop=True)
    dq = {
        "arrival_date": day.isoformat(),
        "rows_read": len(df),
        "rows_passed": len(curated),
        "rows_rejected": len(rejected),
        "by_reason": rejected["reject_reason"].value_counts().to_dict(),
        "outliers_flagged": int(curated["is_outlier"].sum()),
    }
    return curated, rejected, dq


def run(day, base="data"):
    """Clean one date under base (a local folder or s3://bucket)."""
    part = f"arrival_date={day.isoformat()}"
    records = [r for f in storage.list_files(f"{base}/raw/{part}/", ".json") if "commodity=" in f
               for r in json.loads(storage.read_bytes(f))]
    curated, rejected, dq = clean(records, day, load_config())
    storage.write_parquet(curated, f"{base}/curated/{part}/prices.parquet")
    storage.write_parquet(rejected, f"{base}/rejected/{part}/rejected.parquet")
    storage.write_bytes(f"{base}/dq/{part}/dq_summary.json", json.dumps(dq).encode("utf-8"))
    return curated, dq

if __name__ == "__main__":
    print(json.dumps(run(date.fromisoformat(sys.argv[1]))[1], indent=1))
