
### Architecture, before and after

**Before**

```mermaid
%%{init: {"flowchart": {"htmlLabels": false}}}%%
flowchart TD
    A["Fetch ticket + order"] --> B["Large system prompt"]
    B --> C["One LLM call"]
    C --> D["Parse response"]

    classDef bad fill:#8b1a1a,stroke:#e74c3c,color:#ffffff
    class B,C bad
```

**After**

```mermaid
%%{init: {"flowchart": {"htmlLabels": false}}}%%
flowchart TD
    A["Fetch ticket + order"] --> B["Static system prompt"]
    B --> C["Compact input"]
    C --> D["One LLM call"]
    D --> E["Parse response"]

    classDef good fill:#1e5631,stroke:#2ecc71,color:#ffffff
    class B,C,D good
```

| Step | Before | After |
|------|--------|-------|
| System prompt | Run ID, few-shot examples, help center, step-by-step instructions | Instructions and help center only, same on every call |
| Input | Indented order JSON | Thread and one-line order JSON |
| LLM output | ~480 tokens of reasoning | JSON only, ~46 tokens |

The static system prompt is passed as a cached prefix automatically once it
reaches 1,024 tokens. It is about 170 tokens today, so caching is not active.


## Question 2 — architecture, before and after

### Before: four LLM calls per ticket

```mermaid
%%{init: {"flowchart": {"htmlLabels": false}}}%%
flowchart TD
    A["Customer ticket"] --> B["1. Triage (LLM)"]
    B --> C["2. Retrieve (LLM)"]
    C --> D["3. Compose (LLM)"]
    D --> E["4. Audit (LLM)"]
    E --> F["Final resolution"]

    classDef llm fill:#8b1a1a,stroke:#e74c3c,color:#ffffff
    class B,C,D,E llm
```

### After: one LLM call per ticket

```mermaid
%%{init: {"flowchart": {"htmlLabels": false}}}%%
flowchart TD
    A["Customer ticket"] --> B["1. Triage (Python)"]
    B --> C["2. Retrieve (Python)"]
    C --> D["3. Compose (LLM)"]
    D --> E{"4. Audit (Python)"}
    E -->|Pass| F["Final resolution"]
    E -->|Fail| G["Retry compose once"]
    G --> F

    classDef llm fill:#8b1a1a,stroke:#e74c3c,color:#ffffff
    class D llm
```

| Step | Before | After |
|------|--------|-------|
| Triage | LLM reads 120k chars of help center, restates ticket | Python extracts keywords from message and order |
| Retrieve | LLM asked to print 8 articles it cannot see | Python keyword search, top 3 articles |
| Compose | Full reasoning, triage pasted twice | Only LLM call: 3 articles, thread, order; JSON only |
| Audit | LLM reads 80k chars again, rewrites JSON | Python checks JSON, action and article; retries only on failure |
