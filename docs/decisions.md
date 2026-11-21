# Design decisions

**Athena + Parquet instead of a database server.** The data is append-only, about 5,000 rows a day, and queried
a few times a day. Parquet on S3 with Athena costs nothing when idle, needs no server, VPC or patching, and scans
only the columns and days a query needs. A database (RDS, Redshift) would charge by the hour for a mostly idle box.

**Re-fetch the last 3 days every run.** Markets keep reporting for a day or two after the arrival date: on
21 Nov, 20 Nov had 17,121 records while a normal Friday has ~22,000, and second reports for a market (the
`duplicate` rejections) mostly arrive later. Writing each date's files by overwriting makes the re-fetch idempotent —
no duplicates, and the latest version of a day always wins.

**Flag outliers instead of rejecting them.** Extreme prices are sometimes real (premium lots, local shortages)
and sometimes typos (per-kg entries such as 8.2, or a max of 30,002,800). The pipeline cannot tell which, so it keeps
the row with `is_outlier = true` and analytics exclude it with `NOT is_outlier`. Rejection is reserved for rows that
are certainly unusable (missing fields, wrong date, prices out of order).

**Keep one report per natural key, the lowest modal price.** About 1.3% of rows (6,073 in 90 days) repeat
date + market + commodity + variety + grade with different prices — likely separate lots or a corrected re-entry.
The fact grain needs one row per key, so the rule keeps the lowest modal (then min, then max) to be deterministic
and rejects the others with the reason `duplicate`, so nothing disappears silently. Measured over the 90 days, the
reports in a group usually share the modal price (median max/min modal ratio 1.00, 90th percentile 1.20), and keeping the
lowest instead of averaging moves commodity averages by at most 0.2% (Garlic) and about 0.0% for the rest.
Averaging the group would be equally valid; keeping a real reported row was preferred over creating a synthetic one.

**Hash surrogate keys.** `md5(state|district|market)` gives the same key on every run and machine, so each day can
be transformed independently — even by concurrent Lambdas — without a sequence table or a lookup of existing keys.
The cost: 32-character keys, and a renamed market gets a new key (SCD Type 2 would be needed to keep its history).

**Conditional writes for dimension upserts.** Three daily manifests arrive seconds apart and trigger three
transforms that update the same `dim_market` file. Each writes with `If-Match` on the ETag it read; on a conflict it
re-reads, re-merges and retries, so no new market is lost. Limiting the Lambda to one concurrent run was the
alternative, but new accounts cannot reserve concurrency.

**A local Ollama model for the advisory.** `qwen2.5:7b` runs free on the laptop; hosted LLM APIs (Bedrock, OpenAI)
cost money per token. A 3B model was tried in an earlier project and invented numbers. The model never writes SQL:
fixed parameterised queries compute the metrics, the model only phrases them, and any number not in the metrics
blocks the answer.

**Lambda + pandas instead of Glue or Spark.** One day is ~5,500 rows and ~1 MB of JSON — pandas cleans it in about
a second. Spark or Glue would add start-up time, cost and complexity for data this small.

**Daily ingest on the laptop instead of Lambda.** The ingest Lambda was built and deployed, but data.gov.in refuses
connections from AWS (`Connection refused` from ap-southeast-2), and the Free plan's region lock blocks Mumbai.
Running the same code on the laptop with Task Scheduler keeps everything after ingestion serverless on AWS; the
cost is that the laptop must be on, softened by the 3-day re-fetch and a start-when-available task setting.

**One request per commodity-day with `limit=10000`.** The API's offset paging is not stable: paging one day in
pages of 1,000 returned 1,089 repeated rows. A commodity-day is under 1,000 rows, so a single large page avoids
paging entirely.
