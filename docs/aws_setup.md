# AWS setup

Region `ap-southeast-2` (the Free plan locks the account to one region). Bucket `mandi-pipeline-rishiraj`.

## Daily ingestion: why it runs on the laptop

The plan was a Lambda (`ingest_daily`) started by EventBridge Scheduler at 07:00 IST. It was built and deployed,
but every request from Lambda to `api.data.gov.in` failed with `[Errno 111] Connection refused` — the same calls
succeed from India. Moving the Lambda to Mumbai (`ap-south-1`) is not possible: the Free plan's service control
policy denies every other region.

So the daily ingest runs on the laptop and writes straight to S3; everything after that stays on AWS:

```text
Task Scheduler 07:00 IST ── python -m ingest.daily ──> s3://…/raw/arrival_date=…/_manifest.json
                                  │ on failure                       │ S3 event
                                  └──> SNS mandi-alerts (email)      └──> Lambda transform_day ──> Athena
```

- `infra/register_daily_task.ps1` registers the task once (`StartWhenAvailable`, so a missed 7 am run starts when
  the laptop is next on; the 3-day re-fetch then catches up).
- The task runs `pythonw -m ingest.daily` (no console window); the job appends to `data/logs/ingest_daily.log`.
- The API key stays in `.env`; S3 and SNS use the laptop's AWS CLI credentials.
- On any failure (`ApiAuthError`, retries exhausted, …) the job publishes to SNS and exits with code 1.
  Tested with a wrong key: HTTP 403 → alert email.

## One-time setup

```bash
BUCKET=mandi-pipeline-rishiraj ALERT_EMAIL=<you> ./infra/setup_aws.sh   # bucket, lifecycle, SNS topic
aws s3 sync data/raw s3://mandi-pipeline-rishiraj/raw/                   # upload the backfill
powershell -File infra\register_daily_task.ps1                           # 07:00 daily task
```

Bucket: public access blocked, SSE-S3 encryption, versioning on; `raw/` moves to Standard-IA after 30 days and
old object versions expire after 7 days.
