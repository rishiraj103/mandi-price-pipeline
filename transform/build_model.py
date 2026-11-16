"""Curated rows for one date -> star schema (dimension upserts + one fact partition)."""
import hashlib
from datetime import date, datetime, timedelta, timezone
import pandas as pd
import yaml

from transform import storage

IST = timezone(timedelta(hours=5, minutes=30))
MARKET_COLS = ["state", "district", "market"]
COMMODITY_COLS = ["commodity", "variety", "grade"]
FACT_COLS = ["date_key", "market_key", "commodity_key", "min_price", "max_price", "modal_price",
             "price_spread", "is_outlier", "load_date"]


def hash_key(df, cols):
    joined = df[cols].astype(str).agg("|".join, axis=1)
    return joined.map(lambda s: hashlib.md5(s.encode("utf-8")).hexdigest())


def build_dim_date(start=date(2023, 1, 1), end=date(2027, 12, 31)):
    d = pd.Series(pd.date_range(start, end, freq="D"))
    return pd.DataFrame({
        "date_key": d.dt.strftime("%Y%m%d").astype("int32"),
        "full_date": d.dt.date,
        "day": d.dt.day.astype("int8"),
        "iso_week": d.dt.isocalendar().week.astype("int8").values,
        "month": d.dt.month.astype("int8"),
        "quarter": d.dt.quarter.astype("int8"),
        "year": d.dt.year.astype("int16"),
        "weekday": d.dt.day_name(),
        "is_weekend": d.dt.dayofweek >= 5,
    })


def market_rows(curated, regions):
    state_region = {s: r for r, states in regions.items() for s in states}
    dim = curated[MARKET_COLS].drop_duplicates()
    return dim.assign(market_key=hash_key(dim, MARKET_COLS),
                      region=dim["state"].map(state_region).fillna("Unknown"))


def commodity_rows(curated, commodities):
    groups = {c["name"]: c["group"] for c in commodities.values()}
    dim = curated[COMMODITY_COLS + ["commodity_code"]].drop_duplicates(COMMODITY_COLS)
    return dim.assign(commodity_key=hash_key(dim, COMMODITY_COLS),
                      commodity_group=dim["commodity"].map(groups))


def upsert(existing, new, key):
    """SCD Type 1: add new members, keep existing ones. Sorted so reruns write identical files."""
    merged = new if existing is None else pd.concat([existing, new])
    return merged.drop_duplicates(key, keep="first").sort_values(key).reset_index(drop=True)


def fact_rows(curated, day):
    return curated.assign(
        date_key=int(day.strftime("%Y%m%d")),
        market_key=hash_key(curated, MARKET_COLS),
        commodity_key=hash_key(curated, COMMODITY_COLS),
        price_spread=curated["max_price"] - curated["min_price"],
        load_date=datetime.now(IST).date().isoformat(),
    )[FACT_COLS].astype({"date_key": "int32"})


def run(curated, day, base="data"):
    """Upsert dims under base/model (a local folder or s3://bucket) and write the day's fact partition."""
    with open("config/regions.yml") as f:
        regions = yaml.safe_load(f)["regions"]
    with open("config/commodities.yml") as f:
        commodities = yaml.safe_load(f)["commodities"]

    for name, rows, key in [("dim_market", market_rows(curated, regions), "market_key"),
                            ("dim_commodity", commodity_rows(curated, commodities), "commodity_key")]:
        storage.update_parquet(f"{base}/model/{name}/{name}.parquet",
                               lambda existing, rows=rows, key=key: upsert(existing, rows, key))

    fact = fact_rows(curated, day)
    storage.write_parquet(fact, f"{base}/model/fact_price_report/arrival_date={day.isoformat()}/part.parquet")
    return fact
