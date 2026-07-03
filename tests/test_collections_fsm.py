"""
test_collections_fsm.py - Collections FSM and safeguard tests.
Verifies transitions, the duplicate-message guard, the escalation gate,
priority ordering, and terminal-state enforcement.
"""

from datetime import date

from factoring.collections_agent import CollectionsAgent
from factoring.collections_fsm import (
    CollectionCase,
    CollectionOutcome,
    CollectionStage,
    MAX_ACTIONS_PER_CASE,
)
from factoring.mock_data import get_debtors, get_invoices


def make_case(**overrides):
    defaults = dict(
        case_id="CASE-T1",
        invoice_id="INV-T1",
        debtor_id="D001",
        open_amount=10000.0,
        factored_amount=8500.0,
        aging_bucket="31-60",
        priority_score=12750.0,
    )
    defaults.update(overrides)
    return CollectionCase(**defaults)


# ---------------------------------------------------------------------------
# Transitions
# ---------------------------------------------------------------------------

def test_happy_path_promise_to_resolved():
    case = make_case()
    assert case.start_outreach() == CollectionOutcome.OK
    outcome, msg = case.send_message("Please pay invoice INV-T1")
    assert outcome == CollectionOutcome.OK and msg is not None
    assert case.stage == CollectionStage.AWAIT_RESPONSE
    assert case.record_promise(date(2026, 7, 10)) == CollectionOutcome.OK
    assert case.resolve() == CollectionOutcome.OK
    assert case.is_terminal()


def test_dispute_path_sets_dilution_reserve():
    case = make_case()
    case.start_outreach()
    case.send_message("Reminder one")
    assert case.record_dispute("goods damaged in transit") == CollectionOutcome.OK
    assert case.stage == CollectionStage.DISPUTE_INTAKE
    assert case.dilution_reserve == case.open_amount
    assert case.resolve("credit memo issued") == CollectionOutcome.OK
    assert case.dilution_reserve == 0.0


def test_broken_promise_returns_to_outreach():
    case = make_case()
    case.start_outreach()
    case.send_message("Reminder one")
    case.record_promise(date(2026, 7, 10))
    assert case.broken_promise() == CollectionOutcome.OK
    assert case.stage == CollectionStage.OUTREACH


def test_illegal_transition_blocked():
    """Cannot resolve straight from PRIORITIZE — must go through the FSM."""
    case = make_case()
    assert case.resolve() == CollectionOutcome.BLOCKED_ILLEGAL_TRANSITION
    assert case.stage == CollectionStage.PRIORITIZE


def test_write_off_only_from_dispute_or_escalation():
    case = make_case()
    case.start_outreach()
    case.send_message("Reminder one")
    assert case.write_off() == CollectionOutcome.BLOCKED_ILLEGAL_TRANSITION
    assert case.stage == CollectionStage.AWAIT_RESPONSE


def test_terminal_case_blocks_everything():
    case = make_case()
    case.start_outreach()
    case.send_message("Reminder one")
    case.record_promise(date(2026, 7, 10))
    case.resolve()
    assert case.start_outreach() == CollectionOutcome.BLOCKED_TERMINAL
    assert case.send_message("zombie message")[0] == CollectionOutcome.BLOCKED_TERMINAL


# ---------------------------------------------------------------------------
# Safeguards
# ---------------------------------------------------------------------------

def test_duplicate_message_blocked():
    """The anti-loop guard: identical dunning content can never be sent twice."""
    case = make_case()
    case.start_outreach()
    outcome, _ = case.send_message("Please pay invoice INV-T1")
    assert outcome == CollectionOutcome.OK
    # Unclear reply → agent tries again with the SAME message
    case.start_outreach()
    outcome, msg = case.send_message("Please pay invoice INV-T1")
    assert outcome == CollectionOutcome.BLOCKED_DUPLICATE_MESSAGE
    assert msg is None
    assert case.outreach_count == 1  # the blocked send did not count


def test_escalation_gate_requires_two_outreaches():
    case = make_case()
    case.start_outreach()
    case.send_message("Reminder one")
    # Only 1 outreach → escalation must be blocked
    assert case.escalate() == CollectionOutcome.BLOCKED_ESCALATION_GATE
    assert case.stage == CollectionStage.AWAIT_RESPONSE
    # Second outreach opens the gate
    case.start_outreach()
    case.send_message("Second, firmer reminder")
    assert case.escalate() == CollectionOutcome.OK
    assert case.stage == CollectionStage.ESCALATE


def test_max_actions_cap():
    case = make_case()
    case.total_actions = MAX_ACTIONS_PER_CASE
    assert case.start_outreach() == CollectionOutcome.BLOCKED_MAX_ACTIONS


def test_blocked_attempts_are_recorded_in_history():
    case = make_case()
    case.resolve()  # illegal from PRIORITIZE
    assert any("BLOCKED" in entry for entry in case.history)


# ---------------------------------------------------------------------------
# Agent: prioritization, drafting, response handling
# ---------------------------------------------------------------------------

def test_prioritize_builds_queue_of_past_due_only():
    agent = CollectionsAgent()
    cases = agent.prioritize(get_invoices(), get_debtors())
    invoice_ids = {c.invoice_id for c in cases}
    # Invoices due in the future must not be in the queue
    assert "INV-1003" not in invoice_ids
    assert "INV-1014" not in invoice_ids
    # The 90+ day, high-dispute-history debtor invoice must be present
    assert "CASE-INV-1011" in {c.case_id for c in cases}


def test_prioritize_orders_by_score():
    agent = CollectionsAgent()
    cases = agent.prioritize(get_invoices(), get_debtors())
    scores = [c.priority_score for c in cases]
    assert scores == sorted(scores, reverse=True)
    # INV-1011: 90+ bucket (3x) and Ironwood has 2 disputes (3x) → top priority
    assert cases[0].invoice_id == "INV-1011"


def test_second_reminder_is_different_message():
    """Templates differ per attempt, so the duplicate guard never fires
    on a legitimate follow-up."""
    agent = CollectionsAgent()
    debtors = get_debtors()
    invoices = {i.invoice_id: i for i in get_invoices()}
    inv = invoices["INV-1011"]
    case = make_case(invoice_id="INV-1011", debtor_id="D004",
                     open_amount=inv.open_amount)

    outcome1, msg1 = agent.run_outreach(case, inv, debtors["D004"])
    outcome2, msg2 = agent.run_outreach(case, inv, debtors["D004"])
    assert outcome1 == CollectionOutcome.OK
    assert outcome2 == CollectionOutcome.OK
    assert msg1 != msg2
    assert case.outreach_count == 2


def test_outreach_recovers_after_blocked_duplicate_send():
    """A blocked duplicate send leaves the case in OUTREACH; the next
    legitimate outreach must still go through."""
    agent = CollectionsAgent()
    debtors = get_debtors()
    invoices = {i.invoice_id: i for i in get_invoices()}
    inv = invoices["INV-1011"]
    case = make_case(invoice_id="INV-1011", debtor_id="D004",
                     open_amount=inv.open_amount)

    outcome, msg1 = agent.run_outreach(case, inv, debtors["D004"])
    assert outcome == CollectionOutcome.OK
    # A looping agent re-attempts the exact same send → blocked mid-OUTREACH
    case.start_outreach()
    blocked, _ = case.send_message(msg1)
    assert blocked == CollectionOutcome.BLOCKED_DUPLICATE_MESSAGE
    assert case.stage == CollectionStage.OUTREACH
    # The next real outreach (different template) still succeeds
    outcome, msg2 = agent.run_outreach(case, inv, debtors["D004"])
    assert outcome == CollectionOutcome.OK
    assert msg2 != msg1
    assert case.outreach_count == 2


def test_classify_and_route_responses():
    agent = CollectionsAgent()

    dispute_case = make_case()
    dispute_case.start_outreach()
    dispute_case.send_message("Reminder")
    assert agent.handle_response(dispute_case, "We dispute this — goods were damaged") \
        == CollectionOutcome.OK
    assert dispute_case.stage == CollectionStage.DISPUTE_INTAKE

    promise_case = make_case()
    promise_case.start_outreach()
    promise_case.send_message("Reminder")
    assert agent.handle_response(promise_case, "We will pay by Friday",
                                 date(2026, 7, 10)) == CollectionOutcome.OK
    assert promise_case.stage == CollectionStage.PROMISE_TO_PAY
    assert promise_case.promise_date == date(2026, 7, 10)

    unclear_case = make_case()
    unclear_case.start_outreach()
    unclear_case.send_message("Reminder")
    agent.handle_response(unclear_case, "Received, thanks.")
    assert unclear_case.stage == CollectionStage.AWAIT_RESPONSE
