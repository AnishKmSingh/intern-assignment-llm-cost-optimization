# Question 2 — SupportPipeline

## SupportPipeline architecture

Only `compose` calls the LLM on the normal path. Triage, retrieve and audit
are plain Python, so they cost zero points.

```mermaid
flowchart TD
    A[Customer ticket] --> B["1. Triage (Python)<br/>Extract keywords from message and order"]
    B --> C["2. Retrieve (Python)<br/>Rank articles by keyword overlap, keep top 3"]
    C --> D["3. Compose (LLM)<br/>Only LLM call: returns JSON action + article"]
    D --> E{"4. Audit (Python)<br/>Valid JSON? Allowed action?<br/>Retrieved article?"}
    E -- Pass --> F[Final TicketResolution<br/>action + kb_article]
    E -- Fail --> G["Retry compose once<br/>with all articles"]
    G --> F

    style D fill:#fff3cd,stroke:#d4a017
```

| Step | Baseline | Optimised |
|------|---------:|----------:|
| Triage | 32,679 | 0 |
| Retrieve | 2,478 | 0 |
| Compose | 10,899 | 1,566 |
| Audit | 27,447 | 0 |
| **Total (T-1001)** | **73,503** | **1,566** |
