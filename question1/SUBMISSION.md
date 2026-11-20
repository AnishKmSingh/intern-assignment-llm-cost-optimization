
### Architecture, before and after

**Before**

```mermaid
flowchart TD
    A["Fetch ticket and order"] --> B["Build large system prompt: run ID, few-shot examples, help center, step-by-step instructions"]
    B --> C["One LLM call: ~480 output tokens of reasoning"]
    C --> D["Parse response"]

    classDef bad fill:#8b1a1a,stroke:#e74c3c,color:#ffffff
    class B,C bad
```

**After**

```mermaid
flowchart TD
    A["Fetch ticket and order"] --> B["Static system prompt: instructions and help center, same on every call"]
    B --> C["Compact input: thread and one-line order JSON"]
    C --> D["One LLM call: JSON only, ~46 output tokens"]
    D --> E["Parse response"]

    classDef good fill:#1e5631,stroke:#2ecc71,color:#ffffff
    class B,C,D good
```

The static system prompt is passed as a cached prefix automatically once it
reaches 1,024 tokens. It is about 170 tokens today, so caching is not active.




## Question 2 — architecture, before and after

### Before: four LLM calls per ticket

```mermaid
flowchart TD
    A["Customer ticket"] --> B["1. Triage - LLM call 1: 120k chars of help center"]
    B --> C["2. Retrieve - LLM call 2: print 8 articles it cannot see"]
    C --> D["3. Compose - LLM call 3: full reasoning, triage pasted twice"]
    D --> E["4. Audit - LLM call 4: 80k chars of help center again"]
    E --> F["Final resolution"]

    classDef llm fill:#8b1a1a,stroke:#e74c3c,color:#ffffff
    class B,C,D,E llm
```

### After: one LLM call per ticket

```mermaid
flowchart TD
    A["Customer ticket"] --> B["1. Triage - Python keywords"]
    B --> C["2. Retrieve - Python top 3 articles"]
    C --> D["3. Compose - the only LLM call"]
    D --> E{"4. Audit - Python check"}
    E -->|Pass| F["Final resolution: action and kb_article"]
    E -->|Fail| G["Retry compose once with all articles"]
    G --> F

    classDef llm fill:#8b1a1a,stroke:#e74c3c,color:#ffffff
    class D llm
```
