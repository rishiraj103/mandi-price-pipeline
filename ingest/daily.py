"""Daily ingestion, run on the laptop by Windows Task Scheduler at 07:00 IST.

data.gov.in refuses connections from AWS (see docs/decisions.md), so this replaces the planned Lambda.
Fetches yesterday and the 2 days before into s3://$S3_BUCKET/raw/; each manifest triggers transform_day.
Re-fetching 3 days picks up late prices; files are overwritten, so reruns never duplicate.
On any failure it emails through the SNS topic $ALERT_TOPIC_ARN and exits non-zero.

Usage: python -m ingest.daily
"""
import logging
import os
import sys
from datetime import datetime, timedelta

import boto3
from dotenv import load_dotenv

from ingest.api_client import MandiApiClient
from ingest.backfill import IST, RESOURCE_ID, ingest_dates, load_commodities

DAYS_BACK = 3
log = logging.getLogger("ingest.daily")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv(".env")
    today = datetime.now(IST).date()
    dates = [today - timedelta(days=i) for i in range(DAYS_BACK, 0, -1)]
    try:
        client = MandiApiClient(os.environ["DATA_GOV_API_KEY"], RESOURCE_ID)
        failed = ingest_dates(client, dates, load_commodities(), f"s3://{os.environ['S3_BUCKET']}/raw")
        if failed:
            raise RuntimeError(f"{len(failed)} fetches failed: {[(d.isoformat(), c) for d, c in failed]}")
    except Exception as exc:
        log.exception("daily ingest failed")
        boto3.client("sns").publish(TopicArn=os.environ["ALERT_TOPIC_ARN"],
                                    Subject="Mandi pipeline: daily ingest failed",
                                    Message=f"Run for {[d.isoformat() for d in dates]} failed:\n{exc}")
        sys.exit(1)
    log.info("daily ingest ok: %s", [d.isoformat() for d in dates])


if __name__ == "__main__":
    main()
