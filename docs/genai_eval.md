# GenAI evaluation — weekly advisory

Model `qwen2.5:7b` on local Ollama, temperature 0.1. Week 14–20 Nov 2026, metrics from Athena.
Each answer was read by hand against its metrics. Full runs (metrics, drafts, timings) were saved at evaluation time.

| # | Pair | Reports | Change | Number check | All numbers traceable? | Direction word right? | Useful (1–5) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Onion / Maharashtra | 463 | +6.6% | passed | yes | yes ("up 6.6%") | 4 |
| 2 | Potato / Uttar Pradesh | 602 | +3.2% | passed | yes | yes ("up 3.2%") | 3 |
| 3 | Tomato / Karnataka | 98 | +21.4% | passed | yes | yes ("up 21.4%") | 4 |
| 4 | Wheat / Madhya Pradesh | 1,654 | +0.6% | **blocked** | no — wrote "up 6%" | yes | — (metrics shown instead) |
| 5 | Garlic / Rajasthan | 64 | −0.4% | **blocked** | no — wrote "down 4%" | yes | — (metrics shown instead) |

**Result: 3 of 5 answers fully traceable; the other 2 were caught by the number check and never shown.**

## What went wrong

- **Small percentages lose their leading zero.** Both failures are the model turning 0.6 into 6 and −0.4 into 4.
  These are exactly the errors that would mislead a trader (a flat week presented as a 6% rise), and the strict
  check is what stopped them.
- **The spread is misdescribed.** The metric is the average gap between min and max price *within* one market's
  report (named `avg_gap_between_min_and_max_price_within_a_market`). Answers 1, 3 and 4 still called it the gap
  "between the highest and lowest markets". The number is right, the explanation is not — the number check
  cannot catch this kind of error.
- **Weak judgement on risk.** Answer 2 calls a ₹74 gap "wide" when the average price is ₹673; the model has no
  sense of what is normal for a commodity.

## What worked

- Every "up/down" matched the sign of the change.
- The three best markets and their prices were copied exactly in all five answers.
- No answer invented a market, a date or a price.
- About 14 s per answer on a laptop, ~450 prompt and ~100 output tokens.

## Possible improvements (not done)

Give the change as text (`"change": "+0.6%"`), add a precomputed `spread_level` ("low"/"high" vs the
commodity's usual spread), and spell out the meaning of each metric in the prompt.
