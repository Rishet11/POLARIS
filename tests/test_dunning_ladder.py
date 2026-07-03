"""
test_dunning_ladder.py - Channel-aware dunning ladder (A4).
1st touch WhatsApp, 2nd email, escalation phone — deterministic by FSM
state. EN/ES canned templates. Existing guards (duplicate-hash,
escalation gate, action cap) must still fire unchanged.
"""

from datetime import date

from factoring.collections_agent import CollectionsAgent
from factoring.collections_fsm import (
    CollectionCase,
    CollectionOutcome,
    CollectionStage,
    DUNNING_CHANNEL_LADDER,
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
# Ladder ordering
# ---------------------------------------------------------------------------

def test_ladder_constant_is_whatsapp_email_phone():
    assert DUNNING_CHANNEL_LADDER == ["whatsapp", "email", "phone"]


def test_first_touch_is_whatsapp():
    case = make_case()
    assert case.current_channel() == "whatsapp"


def test_second_touch_is_email():
    case = make_case()
    case.start_outreach()
    case.send_message("First reminder")
    assert case.current_channel() == "email"


def test_third_plus_touch_is_phone():
    case = make_case()
    case.start_outreach()
    case.send_message("First reminder")
    case.start_outreach()
    case.send_message("Second reminder")
    assert case.current_channel() == "phone"


def test_send_message_records_channel_used():
    case = make_case()
    case.start_outreach()
    outcome, _ = case.send_message("First reminder")
    assert outcome == CollectionOutcome.OK
    assert case.channel_history == ["whatsapp"]

    case.start_outreach()
    case.send_message("Second reminder")
    assert case.channel_history == ["whatsapp", "email"]


def test_explicit_channel_override_is_recorded():
    case = make_case()
    case.start_outreach()
    case.send_message("First reminder", channel="email")
    assert case.channel_history == ["email"]


# ---------------------------------------------------------------------------
# Guards unchanged
# ---------------------------------------------------------------------------

def test_duplicate_message_still_blocked_with_channel_ladder():
    case = make_case()
    case.start_outreach()
    outcome, _ = case.send_message("Please pay invoice INV-T1")
    assert outcome == CollectionOutcome.OK
    case.start_outreach()
    outcome, msg = case.send_message("Please pay invoice INV-T1")
    assert outcome == CollectionOutcome.BLOCKED_DUPLICATE_MESSAGE
    assert msg is None
    # Blocked send must not record a channel
    assert case.channel_history == ["whatsapp"]


def test_escalation_gate_still_requires_two_outreaches():
    case = make_case()
    case.start_outreach()
    case.send_message("Reminder one")
    assert case.escalate() == CollectionOutcome.BLOCKED_ESCALATION_GATE
    case.start_outreach()
    case.send_message("Second, firmer reminder")
    assert case.escalate() == CollectionOutcome.OK


def test_max_actions_cap_still_enforced():
    from factoring.collections_fsm import MAX_ACTIONS_PER_CASE
    case = make_case()
    case.total_actions = MAX_ACTIONS_PER_CASE
    assert case.start_outreach() == CollectionOutcome.BLOCKED_MAX_ACTIONS


# ---------------------------------------------------------------------------
# EN/ES templates
#
# _template is tested directly (not via draft_reminder/run_outreach) because
# those methods hand off to the configured LLM when DEMO_MODE is off, and in
# the test environment conftest.py mocks the model with a generic canned
# response rather than the real template text.
# ---------------------------------------------------------------------------

def test_template_default_is_english():
    debtors = get_debtors()
    invoices = {i.invoice_id: i for i in get_invoices()}
    inv = invoices["INV-1011"]
    case = make_case(invoice_id="INV-1011", debtor_id="D004", open_amount=inv.open_amount)
    message = CollectionsAgent._template(case, inv, debtors["D004"], attempt=1)
    assert "invoice" in message.lower()


def test_template_spanish_selected_via_language_param():
    debtors = get_debtors()
    invoices = {i.invoice_id: i for i in get_invoices()}
    inv = invoices["INV-1011"]
    case = make_case(invoice_id="INV-1011", debtor_id="D004", open_amount=inv.open_amount)
    message = CollectionsAgent._template(case, inv, debtors["D004"], attempt=1, language="es")
    assert "factura" in message.lower()


def test_template_spanish_second_notice_differs_from_first():
    debtors = get_debtors()
    invoices = {i.invoice_id: i for i in get_invoices()}
    inv = invoices["INV-1011"]
    case = make_case(invoice_id="INV-1011", debtor_id="D004", open_amount=inv.open_amount)
    first = CollectionsAgent._template(case, inv, debtors["D004"], attempt=1, language="es")
    second = CollectionsAgent._template(case, inv, debtors["D004"], attempt=2, language="es")
    assert first != second
    assert "factura" in second.lower()


def test_run_outreach_tags_channel_on_the_ladder():
    agent = CollectionsAgent()
    debtors = get_debtors()
    invoices = {i.invoice_id: i for i in get_invoices()}
    inv = invoices["INV-1011"]
    case = make_case(invoice_id="INV-1011", debtor_id="D004", open_amount=inv.open_amount)

    outcome, msg = agent.run_outreach(case, inv, debtors["D004"], language="es")
    assert outcome == CollectionOutcome.OK
    assert msg is not None
    assert case.channel_history == ["whatsapp"]

    outcome2, msg2 = agent.run_outreach(case, inv, debtors["D004"], language="es")
    assert outcome2 == CollectionOutcome.OK
    assert case.channel_history == ["whatsapp", "email"]
