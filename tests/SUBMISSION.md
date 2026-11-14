# ShopAssist cost lab — submission

Both agents return the same `action` and `kb_article` as the baseline on all
public tickets and the T-1091 holdout, at a fraction of the cost.

| Track | Baseline (T-1001) | Optimised (T-1001) | Target | Total, 4 public tickets |
|-------|------------------:|-------------------:|-------:|------------------------:|
| Q1    | 8,841             | 1,854              | ≤ 3,000 | 6,930 (was 35,418)     |
| Q2    | 73,503            | 1,566              | ≤ 2,500 | 5,736                  |

`points = uncached_input × 3 + cached_input × 0.3 + output × 15`

## Question 1 — single call

### What changed
1. **JSON-only output.** The baseline asked the model to think step by step and
   write full reasoning, which produced about 480 output tokens at 15 points
   each. The prompt now asks for the JSON object only (about 40 tokens).
2. **Static system prompt.** Removed the random run id, so the system prompt is
   byte-identical on every call and is a valid cache prefix.
3. **Smaller input.** Removed the few-shot examples (the help-center articles
   already state the rules) and sent the order snapshot as single-line JSON.

### Points breakdown — T-1001

| Call          | Input | Cached | Output | Points |
|---------------|------:|-------:|-------:|-------:|
| Baseline      | 527   | 0      | 484    | 8,841  |
| handle_ticket | 388   | 0      | 46     | 388×3 + 46×15 = **1,854** |

Other public tickets: T-1002 1,731, T-1003 1,692, T-1004 1,653.

## Question 2 — four-node pipeline

### What changed
The four nodes are kept, but only `compose` calls the LLM.

1. **Triage (Python).** Builds search terms from the customer's messages and the
   order facts.
2. **Retrieve (Python).** Ranks the help-center articles by keyword overlap and
   keeps the top 3. The 210k-token help center is never sent to the model.
3. **Compose (LLM).** One call with the 3 articles, the thread and the order
   snapshot, returning JSON only.
4. **Audit (Python).** Checks that the output parses, the action is one of the
   four allowed, and the article is one that was retrieved. Only if this fails
   does it retry once with every article.

### Points breakdown

Baseline, T-1001 (73,503 total):

| Call     | Input | Output | Points |
|----------|------:|-------:|-------:|
| triage   | 8,453 | 488    | 32,679 |
| retrieve | 596   | 46     | 2,478  |
| compose  | 1,193 | 488    | 10,899 |
| audit    | 6,719 | 486    | 27,447 |

Optimised:

| Ticket | Path | Call | Input | Cached | Output | Points |
|--------|------|------|------:|-------:|-------:|-------:|
| T-1001 | Physical refund | compose | 292 | 0 | 46 | 292×3 + 46×15 = **1,566** |
| T-1003 | Escalation to Tier 2 | compose | 266 | 0 | 39 | 266×3 + 39×15 = **1,383** |

Other public tickets: T-1002 1,443, T-1004 1,344.

## Notes

- **Caching is not active.** The real help-center articles total about 170
  tokens, below the 1,024-token minimum for a cached prefix. The Q1 agent passes
  `cached_prefix` automatically once the static prompt reaches that size. I did
  not pad the prompt just to trigger the discount.
- **The local simulator decides from the order snapshot alone.** Sending only
  the snapshot would score lower, but a real model needs the thread and the
  articles, so both are kept.
- **Tests.** The two `test_baseline_cost_is_high` tests asserted the old high
  cost, so I replaced them with tests for the targets (Q1 ≤ 3,000, Q2 ≤ 2,500
  per public ticket) and a test that retrieval returns the expected article for
  every ticket. `pytest -q` gives 7 passed.

## Run

```bash
pip install -r requirements.txt
pytest -q
python question1/run.py
python question2/run.py
```
