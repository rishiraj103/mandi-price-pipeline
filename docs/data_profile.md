# Data profile

Sample: 14–20 Nov 2026, the 10 commodities in scope, all states — **31,801 rows**, 28 states, 2,049 markets.
Produced by `python -m tools.profile --end 2026-11-20 --days 7`.

## Problems found and rules

| Check | Count | Rule |
| --- | --- | --- |
| Empty required fields | 0 | reject `missing_field` (kept for safety) |
| Dates not `dd/mm/yyyy` | 0 | reject `bad_date` (also future dates / not the requested date) |
| Price not a number | 0 | reject `price_not_number` (old records store prices as text, so parse with `to_numeric`) |
| Any price ≤ 0 | 2 | reject `non_positive_price` |
| min > modal, modal > max, min > max | 0 / 0 / 0 | reject `price_order` |
| Exact duplicate rows | 0 | — |
| Duplicates on (date, state, district, market, commodity, variety, grade) | 490 extra rows in 489 groups, **all with different prices** | keep one (lowest modal, then min, then max — deterministic), reject the rest as `duplicate` |
| Modal price < ₹100/quintal (e.g. 0.01, 1.2, 8.2) | 87 | **flag** `is_outlier` (likely entered per kg); handled by the outlier rule |
| max price > 5× the row's own modal (typos, e.g. max 30,002,800 vs modal 2,600) | 251 in 90 days | **flag** `is_outlier`; one such row pushed Wheat's average spread to 80% of modal |
| min price < 1/5 of modal (e.g. Onion min 200, modal 3,000) | ~3,000 in 90 days, mostly big MP/Maharashtra APMCs | keep — damaged lots in real auctions |
| Leading/trailing spaces | 1,961 in `Market`, 25 in `District` | standardise: trim |
| Double internal spaces (`Ashta  APMC` vs `Ashta APMC`) | 1 market pair | standardise: collapse whitespace |
| Market names differing only by case | 0 | none — names are already consistently cased, so **no title-casing** (it would break `NCT of Delhi`, `APMC`) |
| Commodity code per commodity | exactly 1 each | keep `commodity_code` from the data |

## Distributions

Modal price (₹/quintal): Wheat median 2,726 (tight, std 316); Onion 4,400; Potato 1,200; Tomato 2,500;
Garlic 13,100 (widest, std 6,809). Every commodity except Wheat, Rice and Ginger has a 1st percentile far below
its median — the per-kg entries above.

- **Grade**: 12 values — `Local` 12,183, `FAQ` 11,945, `Medium`, `Grade A/B/C`, `Non-FAQ`, `Large`, `Small`, `Grade Range-1/2/3`.
- **Variety** count per commodity: Wheat 47, Rice 42, Onion 26, Banana 24, Potato 13, Garlic 7, Cauliflower 6, Tomato 6, Green Chilli 3, Ginger 2.
- **Rows per day** (10 commodities): weekdays ~5,500, Saturday 3,417, Sunday 2,104; 20/11 only 3,957 (still filling).
