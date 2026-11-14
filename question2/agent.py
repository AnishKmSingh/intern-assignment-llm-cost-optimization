from __future__ import annotations

import json
import re
from dataclasses import dataclass

from shared.billing import CostSession
from shared.kb import article_ids, load_article
from shared.llm import ChatMessage, LlmClient
from shared.tools import format_thread, get_order, get_ticket

from question1.agent import compact_snapshot, parse_resolution

ACTIONS = {"REFUND", "REPLACE", "SEND_ARTICLE", "ESCALATE_TIER2"}
TOP_K = 3

_INSTRUCTIONS = "\n".join(
    [
        "You are ShopAssist, a Tier-1 e-commerce support copilot.",
        "Pick one action: REFUND, REPLACE, SEND_ARTICLE or ESCALATE_TIER2, "
        "and cite the id of the article that backs it.",
        "Reply with JSON only, no other text: "
        '{"action":"...","kb_article":"<article id>","customer_reply":"<one sentence>"}',
    ]
)

_STOPWORDS = {
    "a", "an", "and", "are", "for", "from", "i", "if", "in", "is", "it", "may",
    "my", "no", "not", "now", "of", "on", "or", "out", "please", "thanks",
    "the", "they", "to", "your", "false", "true", "ago",
}


def _stem(word: str) -> str:
    for suffix in ("ized", "ised", "ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def _terms(text: str) -> set[str]:
    words = re.findall(r"[a-z]+", text.lower())
    return {_stem(w) for w in words if w not in _STOPWORDS and len(w) > 2}


@dataclass
class TicketResolution:
    action: str
    kb_article: str


class SupportPipeline:
    """
    Same product as Question 1: triage -> retrieve -> compose -> audit.

    Only `compose` calls the LLM. Triage, retrieval and audit are plain Python,
    so they cost zero points. The 210k-token help center is never sent to the
    model; only the few articles that match the ticket are.
    """

    def __init__(self, session: CostSession | None = None):
        self.session = session or CostSession()
        self.llm = LlmClient(self.session)

    def handle_ticket(self, ticket_id: str) -> TicketResolution:
        ticket = get_ticket(ticket_id)
        order = get_order(ticket["order_id"])
        thread = format_thread(ticket)
        snapshot = compact_snapshot(order)

        query = self._triage(ticket, order)
        retrieved = self._retrieve(query)
        draft = self._compose(thread, snapshot, retrieved)
        return self._audit(draft, thread, snapshot, retrieved)

    # Node 1: triage (no LLM). Build the search terms for this ticket.
    def _triage(self, ticket: dict, order: dict) -> set[str]:
        customer_text = " ".join(
            m["text"] for m in ticket["messages"] if m["from"] == "customer"
        )
        # Order flags that are set, e.g. "customized", "damage_reported".
        facts = [k for k, v in order.items() if v is True]
        facts += [str(order.get("product_type", "")), str(order.get("title", ""))]
        return _terms(customer_text + " " + " ".join(facts))

    # Node 2: retrieve (no LLM). Rank articles by term overlap, keep the top few.
    def _retrieve(self, query: set[str], k: int = TOP_K) -> list[str]:
        def score(aid: str) -> int:
            return len(query & _terms(aid.replace("-", " ") + " " + load_article(aid)))

        ranked = sorted(article_ids(), key=lambda aid: (-score(aid), aid))
        return ranked[:k]

    # Node 3: compose (the only LLM call on the normal path).
    def _compose(
        self, thread: str, snapshot: str, retrieved: list[str], label: str = "compose"
    ) -> str:
        articles = "\n".join(load_article(aid).strip() for aid in retrieved)
        messages = [
            ChatMessage("system", _INSTRUCTIONS),
            ChatMessage(
                "user",
                "\n".join(
                    [
                        f"ARTICLES:\n{articles}",
                        f"THREAD:\n{thread}",
                        f"ORDER_SNAPSHOT:\n{snapshot}\nEND_SNAPSHOT",
                    ]
                ),
            ),
        ]
        return self.llm.chat(label, messages)

    # Node 4: audit (no LLM unless the draft is invalid).
    def _audit(
        self, draft: str, thread: str, snapshot: str, retrieved: list[str]
    ) -> TicketResolution:
        resolution = self._validate(draft, retrieved)
        if resolution is None:
            # Rare path: retry once with every article in view.
            everything = article_ids()
            draft = self._compose(thread, snapshot, everything, label="compose_retry")
            resolution = self._validate(draft, everything)
        if resolution is None:
            raise ValueError(f"Model output failed audit:\n{draft[:400]}")
        return resolution

    @staticmethod
    def _validate(draft: str, allowed_articles: list[str]) -> TicketResolution | None:
        try:
            parsed = parse_resolution(draft)
        except (ValueError, KeyError, json.JSONDecodeError):
            return None
        if parsed.action not in ACTIONS or parsed.kb_article not in allowed_articles:
            return None
        return TicketResolution(parsed.action, parsed.kb_article)
