"""
test_fsm.py - Comprehensive FSM transition and terminal outcome tests for POLARIS.
Validates all 13 FSM transitions and 4 terminal outcomes of MasterAgent and ConversationState.
"""

import pytest
from state import Stage, TerminalState, Decision, ConversationState
from master_agent import MasterAgent


# =============================================================================
# FSM TRANSITION TESTS
# =============================================================================

def test_transition_intro_to_need_discovery():
    """1. INTRO -> NEED_DISCOVERY (Initial greeting)"""
    agent = MasterAgent()
    assert agent.get_state().stage == Stage.INTRO

    response, state = agent.process_message("Hello there")
    assert state.stage == Stage.NEED_DISCOVERY
    assert state.customer_phone is None
    assert "mobile number" in response.lower()


def test_transition_need_discovery_to_offer_presentation():
    """2. NEED_DISCOVERY -> OFFER_PRESENTATION (Pre-approved limit found, e.g. Rahul Sharma)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    assert agent.get_state().stage == Stage.NEED_DISCOVERY

    response, state = agent.process_message("My phone number is 9876543210")
    assert state.stage == Stage.OFFER_PRESENTATION
    assert state.customer_name == "Rahul Sharma"
    assert state.preapproved_limit == 500000.0
    assert "pre-approved" in response.lower()


def test_transition_need_discovery_to_end_loan_rejected():
    """3. NEED_DISCOVERY -> END with TerminalState.LOAN_REJECTED (Low credit score, Vikram Singh)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    assert agent.get_state().stage == Stage.NEED_DISCOVERY

    response, state = agent.process_message("My phone number is 9876543213")
    assert state.stage == Stage.END
    assert state.terminal_state == TerminalState.LOAN_REJECTED
    assert "minimum credit score" in response.lower()


def test_transition_need_discovery_to_end_customer_dropped():
    """4. NEED_DISCOVERY -> END with TerminalState.CUSTOMER_DROPPED (Phone not found)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    assert agent.get_state().stage == Stage.NEED_DISCOVERY

    response, state = agent.process_message("My phone number is 9999999999")
    assert state.stage == Stage.END
    assert state.terminal_state == TerminalState.CUSTOMER_DROPPED
    assert "couldn't find your profile" in response.lower()


def test_transition_offer_presentation_to_end_customer_dropped():
    """5. OFFER_PRESENTATION -> END with TerminalState.CUSTOMER_DROPPED (Customer declines offer)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    agent.process_message("My phone is 9876543210")
    assert agent.get_state().stage == Stage.OFFER_PRESENTATION

    response, state = agent.process_message("No, not interested")
    assert state.stage == Stage.END
    assert state.terminal_state == TerminalState.CUSTOMER_DROPPED
    assert "thank you for considering" in response.lower()


def test_transition_offer_presentation_to_kyc_verification():
    """6. OFFER_PRESENTATION -> KYC_VERIFICATION (Transitioning to KYC during normal request)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    agent.process_message("My phone is 9876543210")
    assert agent.get_state().stage == Stage.OFFER_PRESENTATION

    called_with_kyc = False
    original_handle_kyc = agent._handle_kyc_verification

    def mock_handle_kyc_verification(user_message):
        nonlocal called_with_kyc
        if agent.state.stage == Stage.KYC_VERIFICATION:
            called_with_kyc = True
        return original_handle_kyc(user_message)

    agent._handle_kyc_verification = mock_handle_kyc_verification

    agent.process_message("I'd like to get 300000 for 24 months")
    assert called_with_kyc is True


def test_transition_kyc_verification_to_underwriting():
    """7. KYC_VERIFICATION -> UNDERWRITING (KYC verified and moves to underwriting checks)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    agent.process_message("My phone is 9876543210")
    assert agent.get_state().stage == Stage.OFFER_PRESENTATION

    called_with_underwriting = False
    original_handle_underwriting = agent._handle_underwriting

    def mock_handle_underwriting(user_message):
        nonlocal called_with_underwriting
        if agent.state.stage == Stage.UNDERWRITING:
            called_with_underwriting = True
        return original_handle_underwriting(user_message)

    agent._handle_underwriting = mock_handle_underwriting

    agent.process_message("I'd like to get 300000 for 24 months")
    assert called_with_underwriting is True
    assert agent.state.kyc_verified is True
    assert agent.state.pan_number is not None


def test_transition_kyc_verification_to_end_loan_rejected():
    """8. KYC_VERIFICATION -> END with TerminalState.LOAN_REJECTED (KYC verification fails, e.g. Sneha Reddy)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    # Sneha Reddy (9876543214) has kyc_verified=False in mock database
    agent.process_message("My phone is 9876543214")
    assert agent.get_state().stage == Stage.OFFER_PRESENTATION

    response, state = agent.process_message("I'd like to get 300000 for 24 months")
    assert state.stage == Stage.END
    assert state.terminal_state == TerminalState.LOAN_REJECTED
    assert state.kyc_verified is False
    assert "couldn't verify your details" in response.lower()


def test_transition_underwriting_to_sanction():
    """9. UNDERWRITING -> SANCTION (Approved instantly when requested amount <= preapproved limit)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    agent.process_message("My phone is 9876543210")  # preapproved limit 500,000

    called_with_sanction = False
    original_handle_sanction = agent._handle_sanction

    def mock_handle_sanction(user_message):
        nonlocal called_with_sanction
        if agent.state.stage == Stage.SANCTION:
            called_with_sanction = True
        return original_handle_sanction(user_message)

    agent._handle_sanction = mock_handle_sanction

    agent.process_message("I'd like to get 300000 for 24 months")
    assert called_with_sanction is True
    assert agent.state.stage == Stage.END
    assert agent.state.terminal_state == TerminalState.LOAN_SANCTIONED
    assert agent.state.decision == Decision.APPROVED


def test_transition_underwriting_to_document_collection():
    """10. UNDERWRITING -> DOCUMENT_COLLECTION (Decision: NEED_SALARY_SLIP when limit < amount <= 2x limit)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    agent.process_message("My phone is 9876543210")  # preapproved limit 500,000

    # Requesting 600,000 which is > 500,000 and <= 1,000,000
    response, state = agent.process_message("I'd like to get 600000 for 24 months")
    assert state.stage == Stage.DOCUMENT_COLLECTION
    assert state.decision == Decision.NEED_SALARY_SLIP
    assert "salary slip" in response.lower()


def test_transition_underwriting_to_rejection():
    """11. UNDERWRITING -> REJECTION (Decision: REJECTED when amount > 2x limit)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    agent.process_message("My phone is 9876543210")  # preapproved limit 500,000

    called_with_rejection = False
    original_handle_rejection = agent._handle_rejection

    def mock_handle_rejection(user_message):
        nonlocal called_with_rejection
        if agent.state.stage == Stage.REJECTION:
            called_with_rejection = True
        return original_handle_rejection(user_message)

    agent._handle_rejection = mock_handle_rejection

    # Requesting 1,200,000 which is > 2x limit (1,000,000)
    response, state = agent.process_message("I'd like to get 1200000 for 24 months")
    assert called_with_rejection is True
    assert state.stage == Stage.END
    assert state.terminal_state == TerminalState.LOAN_REJECTED
    assert state.decision == Decision.REJECTED
    assert "unable to approve" in response.lower()


def test_transition_document_collection_to_underwriting_system_event():
    """12a. DOCUMENT_COLLECTION -> UNDERWRITING (via SYSTEM_UPLOAD_EVENT)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    agent.process_message("My phone is 9876543210")
    agent.process_message("I'd like to get 600000 for 24 months")
    assert agent.get_state().stage == Stage.DOCUMENT_COLLECTION

    called_with_underwriting = False
    original_handle_underwriting = agent._handle_underwriting

    def mock_handle_underwriting(user_message):
        nonlocal called_with_underwriting
        if agent.state.stage == Stage.UNDERWRITING:
            called_with_underwriting = True
        return original_handle_underwriting(user_message)

    agent._handle_underwriting = mock_handle_underwriting

    agent.process_message("SYSTEM_UPLOAD_EVENT: salary_slip.pdf")
    assert called_with_underwriting is True
    assert agent.state.salary_slip_received is True
    assert agent.state.salary == 85000.0


def test_transition_document_collection_to_underwriting_manual_salary():
    """12b. DOCUMENT_COLLECTION -> UNDERWRITING (via manual salary amount entry)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    agent.process_message("My phone is 9876543210")
    agent.process_message("I'd like to get 600000 for 24 months")
    assert agent.get_state().stage == Stage.DOCUMENT_COLLECTION

    called_with_underwriting = False
    original_handle_underwriting = agent._handle_underwriting

    def mock_handle_underwriting(user_message):
        nonlocal called_with_underwriting
        if agent.state.stage == Stage.UNDERWRITING:
            called_with_underwriting = True
        return original_handle_underwriting(user_message)

    agent._handle_underwriting = mock_handle_underwriting

    agent.process_message("My monthly salary is 85000")
    assert called_with_underwriting is True
    assert agent.state.salary_slip_received is True
    assert agent.state.salary == 85000.0


def test_transition_document_collection_to_end_customer_dropped():
    """13. DOCUMENT_COLLECTION -> END with TerminalState.CUSTOMER_DROPPED (Customer declines)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    agent.process_message("My phone is 9876543210")
    agent.process_message("I'd like to get 600000 for 24 months")
    assert agent.get_state().stage == Stage.DOCUMENT_COLLECTION

    response, state = agent.process_message("I don't have it")
    assert state.stage == Stage.END
    assert state.terminal_state == TerminalState.CUSTOMER_DROPPED
    assert "without income verification" in response.lower()


# =============================================================================
# TERMINAL OUTCOMES TESTS
# =============================================================================

def test_terminal_outcome_loan_sanctioned():
    """1. LOAN_SANCTIONED (Happy path loan approval)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    agent.process_message("My phone is 9876543210")
    response, state = agent.process_message("I want 300000 for 24 months")
    
    assert state.is_terminal() is True
    assert state.terminal_state == TerminalState.LOAN_SANCTIONED
    assert state.stage == Stage.END
    assert "approved" in response.lower() or "congratulations" in response.lower()


def test_terminal_outcome_loan_rejected():
    """2. LOAN_REJECTED (Low credit score / KYC verification failed)"""
    agent = MasterAgent()
    agent.process_message("Hi")
    
    # Check low credit score path
    _, state = agent.process_message("My phone is 9876543213")
    assert state.is_terminal() is True
    assert state.terminal_state == TerminalState.LOAN_REJECTED

    # Check KYC verification failed path
    agent2 = MasterAgent()
    agent2.process_message("Hi")
    agent2.process_message("My phone is 9876543214")
    _, state2 = agent2.process_message("I want 300000 for 24 months")
    assert state2.is_terminal() is True
    assert state2.terminal_state == TerminalState.LOAN_REJECTED


def test_terminal_outcome_customer_dropped():
    """3. CUSTOMER_DROPPED (Declined offer, unregistered customer, or declined document collection)"""
    # Test case a: Unregistered customer
    agent = MasterAgent()
    agent.process_message("Hi")
    _, state = agent.process_message("My phone is 9999999999")
    assert state.is_terminal() is True
    assert state.terminal_state == TerminalState.CUSTOMER_DROPPED

    # Test case b: Declined offer
    agent2 = MasterAgent()
    agent2.process_message("Hi")
    agent2.process_message("My phone is 9876543210")
    _, state2 = agent2.process_message("No, not interested")
    assert state2.is_terminal() is True
    assert state2.terminal_state == TerminalState.CUSTOMER_DROPPED

    # Test case c: Declined document collection
    agent3 = MasterAgent()
    agent3.process_message("Hi")
    agent3.process_message("My phone is 9876543210")
    agent3.process_message("I want 600000 for 24 months")
    _, state3 = agent3.process_message("I can't provide")
    assert state3.is_terminal() is True
    assert state3.terminal_state == TerminalState.CUSTOMER_DROPPED


def test_terminal_outcome_additional_document_required():
    """4. ADDITIONAL_DOCUMENT_REQUIRED terminal state check"""
    agent = MasterAgent()
    state = agent.get_state()
    
    # Set terminal state manually
    state.terminal_state = TerminalState.ADDITIONAL_DOCUMENT_REQUIRED
    assert state.is_terminal() is True

    # Check that process_message triggers safeguard message
    response, final_state = agent.process_message("Any user message")
    assert response == "Conversation ended: ADDITIONAL_DOCUMENT_REQUIRED"
    assert final_state.terminal_state == TerminalState.ADDITIONAL_DOCUMENT_REQUIRED
