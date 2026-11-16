"""Fetch raw API data per date and commodity.

Usage:
    python -m ingest.backfill --days 90            # yesterday and the 89 days before
    python -m ingest.backfill --retry-failed       # rerun dates listed in failed.csv
"""
import argparse
import csv
import json
import logging
import os
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from ingest.api_client import ApiUnavailableError, MandiApiClient

RESOURCE_ID = "35985678-0d79-46b4-9ed6-6f13308a1d24"
IST = timezone(timedelta(hours=5, minutes=30))
PAUSE_SECONDS = 0.5

log = logging.getLogger(__name__)


def load_commodities(path="config/commodities.yml"):
    with open(path) as f:
        return list(yaml.safe_load(f)["commodities"])


def write_text(path, text):
    """Write to a local path or to s3://bucket/key."""
    if path.startswith("s3://"):
        import boto3
        bucket, key = path[5:].split("/", 1)
        boto3.client("s3").put_object(Bucket=bucket, Key=key, Body=text.encode("utf-8"),
                                      ContentType="application/json")
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ingest_date(client, day, commodities, out_dir):
    """Write one JSON file per commodity, then the manifest. Returns the commodities that failed."""
    folder = f"{out_dir}/arrival_date={day.isoformat()}"
    rows, failed = {}, []
    for name in commodities:
        try:
            records = client.fetch_all({"Arrival_Date": day.strftime("%d/%m/%Y"), "Commodity": name})
        except ApiUnavailableError as exc:
            log.error("%s %s failed: %s", day, name, exc)
            failed.append(name)
            continue
        # API order is not stable; sort so a rerun with the same data writes an identical file
        records.sort(key=lambda r: json.dumps(r, sort_keys=True))
        write_text(f"{folder}/commodity={name}.json", json.dumps(records, sort_keys=True))
        rows[name] = len(records)
        log.info("%s %-14s %5d rows", day, name, len(records))
        time.sleep(PAUSE_SECONDS)

    if not failed:  # manifest last: it signals the date is complete (and triggers the transform on AWS)
        manifest = {"arrival_date": day.isoformat(),
                    "fetched_at": datetime.now(IST).isoformat(timespec="seconds"), "rows": rows}
        write_text(f"{folder}/_manifest.json", json.dumps(manifest, indent=1))
    return failed


def ingest_dates(client, dates, commodities, out_dir):
    """Ingest every date; returns a list of (date, commodity) pairs that still failed."""
    return [(d, name) for d in dates for name in ingest_date(client, d, commodities, out_dir)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--end", type=date.fromisoformat, default=datetime.now(IST).date() - timedelta(days=1))
    p.add_argument("--out", default="data/raw")
    p.add_argument("--failed-file", default="data/failed.csv")
    p.add_argument("--retry-failed", action="store_true")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    from dotenv import load_dotenv
    load_dotenv(".env")
    client = MandiApiClient(os.environ["DATA_GOV_API_KEY"], RESOURCE_ID)

    if args.retry_failed:
        with open(args.failed_file) as f:
            dates = sorted({date.fromisoformat(row["date"]) for row in csv.DictReader(f)})
    else:
        dates = [args.end - timedelta(days=i) for i in range(args.days)][::-1]

    # a failed date is retried as a whole so its manifest always lists every commodity
    failed = ingest_dates(client, dates, load_commodities(), args.out)

    Path(args.failed_file).parent.mkdir(parents=True, exist_ok=True)
    with open(args.failed_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "commodity"])
        writer.writerows((d.isoformat(), name) for d, name in failed)
    log.info("done: %d dates, %d failed calls -> %s", len(dates), len(failed), args.failed_file)


if __name__ == "__main__":
    main()
