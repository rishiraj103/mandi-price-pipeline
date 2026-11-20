# Query results (Athena, run 21 Nov 2026)

Data: 23 Aug – 20 Nov 2026, 451,933 fact rows. CSVs in this folder are the full outputs of `sql/analytics/`.

| Query | Rows | Data scanned |
| --- | --- | --- |
| Q1 week-over-week change (8 full weeks) | 2,042 | 5.835 MB |
| Q2 top/bottom 5 markets (7 days) | 1,744 | 0.780 MB |
| Q3 latest price per market (30 days) | 7,612 | 3.327 MB |
| Q4 7-day rolling average and volatility (60 days) | 600 | 2.474 MB |
| Q5 state vs national average (7 days) | 225 | 1.033 MB |
| Q6 missed reporting weekdays (14 days) | 1,671 | 1.442 MB |
| Q7 widest in-market price spread (30 days) | 10 | 1.387 MB |

Validation (`sql/checks/`): orphan keys, duplicate natural keys and bad prices all return **0 rows**.

## Partition pruning

Same query with and without the `arrival_date` filter:

| Query | With filter | Without filter | Reduction |
| --- | --- | --- | --- |
| Q2 (last 7 days) | 0.780 MB | 8.674 MB | 11× |
| Q1 (8 full weeks of 13) | 5.835 MB | 8.659 MB | 1.5× |

Athena reads only the `arrival_date=…` folders a query asks for; the dimension tables are always read in full.

## Spot check against raw JSON

Q3 says Onion at APMC Lasalgaon (Maharashtra, variety Unhali, grade Local) last reported on 2026-11-20 at
min 2,090 / modal 4,300 / max 4,601. The raw file `raw/arrival_date=2026-11-20/commodity=Onion.json` has exactly
`Min_Price 2090, Modal_Price 4300, Max_Price 4601` for `"APMC Lasalgaon "` (trailing space trimmed by cleaning).

## Highlights

- Q7: Garlic has the widest spread inside markets (41% of modal); Wheat the narrowest (8%).
- Q6: some markets report only on certain weekdays (weekly markets), so "missed" days are not always data gaps.

## SQL dialect note

DuckDB turns `current_date - INTERVAL 'n' DAY` into a timestamp, so its string form (`2026-09-26 00:00:00`)
silently dropped the boundary day when compared with the string partition. The queries cast to `date` first,
which gives identical results on DuckDB and Athena.
