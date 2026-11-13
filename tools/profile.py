"""Download one week of in-scope commodities (if missing) and print a data profile.

Usage: python -m tools.profile --end 2026-11-20 --days 7
"""
import argparse
import json
import os
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv

from ingest.api_client import MandiApiClient

RESOURCE_ID = "35985678-0d79-46b4-9ed6-6f13308a1d24"
SAMPLE_DIR = Path("data/sample")
KEY_COLS = ["Arrival_Date", "State", "District", "Market", "Commodity", "Variety", "Grade"]
PRICE_COLS = ["Min_Price", "Max_Price", "Modal_Price"]


def download(dates, commodities):
    load_dotenv(".env")
    client = MandiApiClient(os.environ["DATA_GOV_API_KEY"], RESOURCE_ID)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    for d in dates:
        for name in commodities:
            path = SAMPLE_DIR / f"{d}_{name}.json"
            if path.exists():
                continue
            rows = client.fetch_all({"Arrival_Date": d.strftime("%d/%m/%Y"), "Commodity": name})
            path.write_text(json.dumps(rows))
            time.sleep(0.5)


def profile(df):
    prices = df[PRICE_COLS].apply(pd.to_numeric, errors="coerce")
    not_number = prices.isna() & df[PRICE_COLS].notna()
    parsed_date = pd.to_datetime(df["Arrival_Date"], format="%d/%m/%Y", errors="coerce")
    names = df[["State", "District", "Market"]].drop_duplicates()
    norm = names.assign(k=names["Market"].str.lower().str.replace(r"[^a-z]", "", regex=True))

    print("rows per day:\n", df.groupby("Arrival_Date").size().to_string(), "\n")
    print("rows per commodity:\n", df.groupby("Commodity").size().to_string(), "\n")
    print("nulls / empty strings per column:\n",
          (df.isna() | (df.astype(str).apply(lambda s: s.str.strip()) == "")).sum().to_string(), "\n")
    checks = {
        "exact duplicate rows": df.duplicated().sum(),
        "duplicates on natural key": df.duplicated(KEY_COLS).sum(),
        "natural-key dups with different prices": df.duplicated(KEY_COLS).sum() - df.duplicated().sum(),
        "price not a number (any col)": not_number.any(axis=1).sum(),
        "any price <= 0": (prices <= 0).any(axis=1).sum(),
        "min > modal": (prices.Min_Price > prices.Modal_Price).sum(),
        "modal > max": (prices.Modal_Price > prices.Max_Price).sum(),
        "min > max": (prices.Min_Price > prices.Max_Price).sum(),
        "bad dd/mm/yyyy date": parsed_date.isna().sum(),
        "names with leading/trailing spaces": sum(
            (df[c].astype(str) != df[c].astype(str).str.strip()).sum() for c in KEY_COLS),
        "distinct markets": len(names),
        "markets differing only by case/punctuation": names.shape[0] - norm.drop_duplicates(
            ["State", "District", "k"]).shape[0],
    }
    for k, v in checks.items():
        print(f"{k:45} {v}")
    print("\nmodal price by commodity (Rs/quintal):\n",
          prices.Modal_Price.groupby(df["Commodity"]).describe(percentiles=[.01, .5, .99]).round(0).to_string())
    print("\ndistinct Grade:", df["Grade"].value_counts().to_dict())
    print("distinct Variety per commodity:\n", df.groupby("Commodity")["Variety"].nunique().to_string())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--end", default=str(date.today() - timedelta(days=1)))
    p.add_argument("--days", type=int, default=7)
    args = p.parse_args()
    end = date.fromisoformat(args.end)
    dates = [end - timedelta(days=i) for i in range(args.days)]
    commodities = yaml.safe_load(open("config/commodities.yml"))["commodities"]

    download(dates, commodities)
    files = [SAMPLE_DIR / f"{d}_{c}.json" for d in dates for c in commodities]
    df = pd.DataFrame([r for f in files for r in json.loads(f.read_text())])
    profile(df)


if __name__ == "__main__":
    main()
