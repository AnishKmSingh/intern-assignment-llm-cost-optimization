from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache

from shared.billing import CACHE_MIN_PREFIX, CostSession
from shared.kb import all_articles_blob
from shared.llm import ChatMessage, LlmClient
from shared.tokens import count_tokens
from shared.tools import format_thread, get_order, get_ticket


@dataclass
class TicketResolution:
    action: str
    kb_article: str
    customer_reply: str
    raw_completion: str


def parse_resolution(text: str) -> TicketResolution:
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError(f"No JSON in model output:\n{text[:400]}")
    data = json.loads(m.group())
    return TicketResolution(
        action=str(data["action"]).upper(),
        kb_article=str(data["kb_article"]),
        customer_reply=str(data.get("customer_reply", "")),
        raw_completion=text,
    )


def compact_snapshot(order: dict) -> str:
    """Order facts as single-line JSON (no indent whitespace to pay for)."""
    return json.dumps(order, separators=(",", ":"))


@lru_cache
def system_prompt() -> str:
    """
    Static part of the prompt. It is byte-identical for every ticket (no run id,
    no timestamps), so it is a valid cache prefix.
    """
    return "\n".join(
        [
            "You are ShopAssist, a Tier-1 e-commerce support copilot.",
            "Pick one action: REFUND, REPLACE, SEND_ARTICLE or ESCALATE_TIER2, "
            "and cite the id of the help-center article that backs it.",
            "Reply with JSON only, no other text: "
            '{"action":"...","kb_article":"<article id>","customer_reply":"<one sentence>"}',
            "HELP CENTER:",
            all_articles_blob(),
        ]
    )


@lru_cache
def cacheable_prefix() -> str | None:
    """Prefix to bill at the cached rate, or None if it is under the minimum size."""
    prefix = f"SYSTEM:\n{system_prompt()}"
    return prefix if count_tokens(prefix) >= CACHE_MIN_PREFIX else None


class SupportCopilot:
    """
    ShopAssist Tier-1 copilot (cost-optimised).

    One LLM call per ticket: static instructions + help center first, then the
    ticket thread and order facts. The model returns a short JSON object only.
    """

    def __init__(self, session: CostSession | None = None):
        self.session = session or CostSession()
        self.llm = LlmClient(self.session)

    def build_messages(self, ticket_id: str) -> list[ChatMessage]:
        ticket = get_ticket(ticket_id)
        order = get_order(ticket["order_id"])
        user = "\n".join(
            [
                f"THREAD:\n{format_thread(ticket)}",
                f"ORDER_SNAPSHOT:\n{compact_snapshot(order)}\nEND_SNAPSHOT",
            ]
        )
        return [ChatMessage("system", system_prompt()), ChatMessage("user", user)]

    def handle_ticket(self, ticket_id: str) -> TicketResolution:
        messages = self.build_messages(ticket_id)
        completion = self.llm.chat(
            "handle_ticket", messages, cached_prefix=cacheable_prefix()
        )
        return parse_resolution(completion)
