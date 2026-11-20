### Q1 before: one LLM call with a large prompt and long reasoning (~8,800 points)
<img width="895" height="683" alt="q1-before" src="https://github.com/user-attachments/assets/47a8ca33-1e0e-4ee1-8e6d-199ed53dab88" />


### Q1 after: same single call, static prompt and JSON-only output (~1,850 points)

<img width="862" height="799" alt="q1-after" src="https://github.com/user-attachments/assets/5c0112ba-9118-47df-aff0-df04b5fd32a7" />



### Q2 before: four LLM calls, help center sent twice (~73,500 points)
<img width="1199" height="939" alt="q2-before" src="https://github.com/user-attachments/assets/30669465-ebf8-4672-9aae-c1ca32f7a180" />


### Q2 after: one LLM call, triage, retrieve and audit in Python (~1,500 points)
<img width="1116" height="1116" alt="q2-after" src="https://github.com/user-attachments/assets/9f0a769d-de4a-44f5-b716-c64a3b4ccae1" />


## Results comparison

| Question | Ticket | Before (points) | After (points) | Target | Saving |
|----------|--------|----------------:|---------------:|-------:|-------:|
| Q1 | T-1001 | 8,841 | 1,854 | ≤ 3,000 | 79% |
| Q1 | T-1002 | – | 1,731 | ≤ 3,000 | – |
| Q1 | T-1003 | – | 1,692 | ≤ 3,000 | – |
| Q1 | T-1004 | – | 1,653 | ≤ 3,000 | – |
| **Q1** | **All 4 tickets** | **35,418** | **6,930** | | **80%** |
| Q2 | T-1001 | 73,503 | 1,566 | ≤ 2,500 | 98% |
| Q2 | T-1002 | – | 1,443 | ≤ 2,500 | – |
| Q2 | T-1003 | 73,545 | 1,383 | ≤ 2,500 | 98% |
| Q2 | T-1004 | – | 1,344 | ≤ 2,500 | – |
| **Q2** | **All 4 tickets** | **~294,000** | **5,736** | | **98%** |

All answers (`action`, `kb_article`) are unchanged, and `pytest -q` gives 7 passed.
