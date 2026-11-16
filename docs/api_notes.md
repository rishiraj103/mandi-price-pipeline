# API notes

Resource: `35985678-0d79-46b4-9ed6-6f13308a1d24` — "Variety-wise Daily Market Prices Data of Commodity"
(`https://api.data.gov.in/resource/<id>?api-key=…&format=json&limit=…&offset=…&filters[Field]=value`).
Tested on 21 Nov 2026.

| Question | Answer |
| --- | --- |
| Total records | 83,232,150 |
| Max records per call | 10,000 tested and returned in full (~5 s). A 20,000 request also returned all 17,121 rows of one day, so the cap is ≥ 17k. |
| Response time | 0.1–1 s for small pages; ~1 s per 1,000 rows |
| Commodity + date filter together | works (Onion on 20/11/2026 → 579 rows) |
| State filter | works together with the other two (Onion + 20/11/2026 + Maharashtra → 51 rows) |
| Date filter format | `dd/mm/yyyy` and `dd-mm-yyyy` both work |
| Filter case-sensitivity | **case-sensitive**: `onion` → 0 rows, `Onion` → 579 |
| Rows for one commodity-day | 400–600 for the busiest (Tomato 585, Onion 579, Potato 537 on 20/11) |
| Rows per day (all commodities) | weekdays ~22,000–23,000; Saturday ~13,000; Sunday ~7,800 |
| `total` field | returns the filtered row count, so a `limit=1` call is a cheap count |
| Price field types | JSON numbers (int, sometimes float) in recent data; strings in old (2009) records — parse both |
| Yesterday's count today vs tomorrow | 20/11/2026: 17,121 at 16:33 on 21/11 → _recheck on 22/11_ (Friday 13/11 had 21,674, so late data is likely) |

## Paging pitfall

Paging the same day with `limit=1000` returned 17,121 rows but only **16,032 unique** —
the API's sort order is not stable across pages, so offset paging can repeat and skip rows.
With `limit=10000` all 17,121 rows were unique.

**Decision:** fetch per date × commodity (≤ ~600 rows) with `limit=10000`, so every request is a single
page and offset paging is never actually exercised. `fetch_all` still pages as a safety net.

## Reliability

Occasional hung requests (~1 in 35 calls during the backfill) that end in `ConnectionError`; the retry
succeeded every time. With a 120 s read timeout each hang cost 2 minutes (20 of the first 26 backfill minutes),
so the read timeout is 30 s: a commodity-day normally returns in ~1 s, and the daily Lambda must fit in 5 minutes.

## Commodity names in scope

Exact spellings from 20/11/2026 are in `config/commodities.yml`. Notes: `Ginger(Green)` (not "Ginger"),
`Rice` (separate from `Paddy(Common)`/`Paddy(Basmati)`), `Banana` (separate from `Banana - Green`).
