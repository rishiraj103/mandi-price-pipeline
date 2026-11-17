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
- 90-day backfill (26 Aug – 20 Nov 2026): 90 dates, 0 failed calls.
