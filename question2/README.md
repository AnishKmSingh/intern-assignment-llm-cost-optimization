# Question 2 — SupportPipeline

## Baseline architecture (before)

All four steps called the LLM, and two of them pasted large parts of the
210k-token help center into the prompt. One ticket cost about 73,500 points.

```mermaid
flowchart TD
    A["Customer ticket"] --> B["1. Triage - LLM call 1<br/>Reads ticket + 120k chars of help center<br/>Restates ticket step by step"]
    B --> C["2. Retrieve - LLM call 2<br/>Asked to print 8 articles it cannot see"]
    C --> D["3. Compose - LLM call 3<br/>Full reasoning, triage pasted twice"]
    D --> E["4. Audit - LLM call 4<br/>80k chars of help center again<br/>Double-checks and rewrites JSON"]
    E --> F["Final resolution"]

    style B fill:#f8d7da,stroke:#c0392b
    style C fill:#f8d7da,stroke:#c0392b
    style D fill:#f8d7da,stroke:#c0392b
    style E fill:#f8d7da,stroke:#c0392b
```

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
