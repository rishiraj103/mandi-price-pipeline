"""Transform Lambda: triggered by s3://<bucket>/raw/arrival_date=YYYY-MM-DD/_manifest.json.

Cleans the date and adds it to the star schema, reading from and writing to the same bucket.
Manual run: {"dates": ["2026-11-20"]} (uses the S3_BUCKET environment variable).
"""
import logging
import os
import re
from datetime import date
from urllib.parse import unquote_plus

from transform import build_model, clean_day

log = logging.getLogger()
log.setLevel(logging.INFO)


def dates_from_event(event):
    if "dates" in event:
        return [(os.environ["S3_BUCKET"], date.fromisoformat(d)) for d in event["dates"]]
    out = []
    for record in event["Records"]:
        key = unquote_plus(record["s3"]["object"]["key"])
        out.append((record["s3"]["bucket"]["name"],
                    date.fromisoformat(re.search(r"arrival_date=(\d{4}-\d{2}-\d{2})/", key).group(1))))
    return out


def handler(event, context):
    results = []
    for bucket, day in dates_from_event(event):
        curated, dq = clean_day.run(day, f"s3://{bucket}")
        fact = build_model.run(curated, day, f"s3://{bucket}")
        log.info("%s dq=%s fact_rows=%d", day, dq, len(fact))
        results.append({"arrival_date": day.isoformat(), "fact_rows": len(fact), **dq})
    return results
