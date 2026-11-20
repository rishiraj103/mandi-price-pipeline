# Changelog

## v0.1-setup — 2026-11-12
- Repo layout, requirements, `.env.example`, CI running unit tests on every push.

## v0.2-api-profile — 2026-11-13
- `MandiApiClient` with retries, backoff and `ApiAuthError` / `ApiUnavailableError`.
- API behaviour documented (page size, filters, unstable offset paging); profile of one week of data and cleaning rules.

## v0.3-design — 2026-11-14
- Star schema design: fact grain, hash surrogate keys, SCD Type 1, partitioning by arrival date.

## v0.4-ingest — 2026-11-17
- `ingest_dates` writes raw JSON per date and commodity (sorted, so reruns are byte-identical) and a manifest last.
- Failed calls go to `data/failed.csv`; `--retry-failed` reruns those dates. Read timeout 30 s so hung requests retry fast.
- 90-day backfill (23 Aug – 20 Nov 2026): 90 dates, 0 failed calls.

## v0.5-clean — 2026-11-17
- Rules as pure functions with one test each; rejected rows saved with a reason; daily dq summary.
- Outliers flagged (modal vs national median, and max price > 5x modal), not rejected.

## v0.6-model-local — 2026-11-17
- Star schema as Parquet: dim_date, dim_market, dim_commodity (hash keys, SCD Type 1) and a fact partition per day.
- 451,933 fact rows over 90 days; 0 orphan keys, 0 duplicate keys, 0 bad prices. Q1–Q7 run in DuckDB.

## v0.7-aws-ingest — 2026-11-18
- S3 bucket (encrypted, versioned, private, lifecycle rules) with the 90-day backfill uploaded.
- data.gov.in refuses connections from AWS, so the daily ingest runs on the laptop (Task Scheduler, 07:00 IST)
  and writes straight to S3; failures email through SNS (tested with a wrong key).

## v0.8-aws-transform — 2026-11-18
- `transform_day` Lambda triggered by each `_manifest.json`; conditional S3 writes keep concurrent dimension upserts safe.
- Athena tables with partition projection and a workgroup capped at 100 MB per query.
- Athena counts match local for all 90 dates (451,933 rows); orphan, duplicate and price checks return 0 rows.

## v0.9-analytics — 2026-11-18
- Q1–Q7 on Athena with outputs in `docs/results/`; views `v_weekly_prices`, `v_market_ranking`, `v_latest_price`.
- Validation queries return 0 rows; partition pruning cuts a 7-day query from 8.7 MB to 0.8 MB scanned.

## v0.10-genai — 2026-11-19
- Weekly advisory: fixed parameterised SQL computes the metrics, local Ollama `qwen2.5:7b` writes the note.
- Strict number check: any number not in the metrics hides the answer. 5 pairs hand-checked: 3 fully traceable,
  2 caught by the check (model wrote 6% for 0.6%).

## v0.11-app — 2026-11-20
- Streamlit app with four pages (prices, markets, data quality, advisory) reading the views; `SOURCE=local|athena`.
- Screenshots in `docs/screenshots/` (taken against Athena).
