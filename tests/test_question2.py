from __future__ import annotations

from shared.kb import expanded_help_center_blob
from shared.tokens import count_tokens
from eval.reference import TICKET_EXPECTATIONS
from question2.agent import SupportPipeline

PUBLIC = ["T-1001", "T-1002", "T-1003", "T-1004"]


def test_help_center_exceeds_context():
    assert count_tokens(expanded_help_center_blob()) > 200_000


def test_pipeline_resolves_public_tickets():
    pipe = SupportPipeline()
    for tid in PUBLIC:
        expected = TICKET_EXPECTATIONS[tid]
        got = pipe.handle_ticket(tid)
        assert got.action == expected.action
        assert got.kb_article == expected.kb_article


def test_cost_within_target():
    for tid in PUBLIC:
        pipe = SupportPipeline()
        pipe.handle_ticket(tid)
        assert pipe.session.total_points() <= 2500


def test_retrieval_finds_expected_article():
    from shared.tools import get_order, get_ticket

    pipe = SupportPipeline()
    for tid, expected in TICKET_EXPECTATIONS.items():
        ticket = get_ticket(tid)
        order = get_order(ticket["order_id"])
        assert expected.kb_article in pipe._retrieve(pipe._triage(ticket, order))
