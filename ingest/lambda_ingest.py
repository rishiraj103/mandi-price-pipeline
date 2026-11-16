"""Daily Lambda: fetch yesterday and the 2 days before into s3://$S3_BUCKET/raw/.

Re-fetching 3 days picks up late-arriving prices; files are overwritten, so reruns never duplicate.
Raises if any (date, commodity) still fails after retries, so the CloudWatch Errors alarm fires.
"""
import logging
import os
from datetime import date, datetime, timedelta

import boto3

from ingest.api_client import MandiApiClient
from ingest.backfill import IST, RESOURCE_ID, ingest_dates, load_commodities

DAYS_BACK = 3
logging.getLogger().setLevel(logging.INFO)


def handler(event, context):
    api_key = boto3.client("ssm").get_parameter(
        Name=os.environ.get("API_KEY_PARAM", "/mandi/api_key"), WithDecryption=True)["Parameter"]["Value"]
    client = MandiApiClient(api_key, RESOURCE_ID)

    if "dates" in event:  # manual run, e.g. {"dates": ["2026-11-20"]}
        dates = [date.fromisoformat(d) for d in event["dates"]]
    else:
        today = datetime.now(IST).date()
        dates = [today - timedelta(days=i) for i in range(DAYS_BACK, 0, -1)]

    failed = ingest_dates(client, dates, load_commodities(), f"s3://{os.environ['S3_BUCKET']}/raw")
    if failed:
        raise RuntimeError(f"{len(failed)} fetches failed: {failed}")
    return {"dates": [d.isoformat() for d in dates], "status": "ok"}
