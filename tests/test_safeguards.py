"""
tests/test_safeguards.py - Unit and integration tests validating the security
and robustness safeguards of the POLARIS conversation system.
"""

import os
import pytest
from state import ConversationState, Stage, TerminalState
from master_agent import MasterAgent
from agents.sanction_agent import SanctionAgent, FPDF_AVAILABLE


# =============================================================================
# 1. ANTI-LOOP SAFEGUARD TESTS
# =============================================================================

def test_basic_signature_tracking():
    """
    Verify basic signature tracking on ConversationState:
    - can_call_agent() returns True initially.
    - After calling record_agent_call(), can_call_agent() returns False for the same signature.
    - Verify that total_agent_calls count incremented correctly.
    """
    state = ConversationState()
    agent_name = "TEST_AGENT"
    input_hash = "abc123hash"
    
    # Verify initial state
    assert state.can_call_agent(agent_name, input_hash) is True
    assert state.total_agent_calls == 0
    assert len(state.agent_call_history) == 0
    
    # Record the call signature
    state.record_agent_call(agent_name, input_hash)
    
    # Verify signature tracking updates
    assert state.can_call_agent(agent_name, input_hash) is False
    assert state.total_agent_calls == 1
    assert state.last_agent_called == agent_name
    assert f"{agent_name}:{input_hash}" in state.agent_call_history


def test_anti_loop_verification_agent_direct():
    """
    Directly simulate the flow on MasterAgent's internal handlers to verify the
    anti-loop safeguard for VERIFICATION_AGENT.
    - First call is allowed.
    - Second call with the same input_hash (same phone number) triggers the anti-loop check.
    - MasterAgent should return the specified error message, set Stage.END, and TerminalState.LOAN_REJECTED.
    """
    agent = MasterAgent()
    agent.initialize()
    agent.state.customer_phone = "9876543210"
    
    # First invocation: processes KYC and moves to underwriting checks
    res1 = agent._handle_kyc_verification("Dummy message")
    assert "issue with the verification process" not in res1
    
    # Reset stage to KYC_VERIFICATION (simulating routing back to KYC stage)
    # keeping the agent call history intact
    agent.state.stage = Stage.KYC_VERIFICATION
    agent.state.terminal_state = None
    
    # Second invocation with same phone number triggers safeguard
    res2 = agent._handle_kyc_verification("Dummy message")
    
    assert res2 == "There was an issue with the verification process. Please try again later."
    assert agent.state.stage == Stage.END
    assert agent.state.terminal_state == TerminalState.LOAN_REJECTED


def test_anti_loop_verification_agent_via_process_message():
    """
    Simulate the conversation flow using process_message to verify that
    repeatedly routing to VERIFICATION_AGENT with same inputs triggers the safeguard.
    """
    agent = MasterAgent()
    agent.initialize()
    agent.state.customer_phone = "9876543210"
    agent.state.stage = Stage.KYC_VERIFICATION
    
    # Call 1
    res1, state1 = agent.process_message("Verify my KYC")
    assert "issue with the verification process" not in res1
    
    # Re-route conversation state back to KYC stage to simulate a loop, resetting terminal status
    agent.state.stage = Stage.KYC_VERIFICATION
    agent.state.terminal_state = None
    
    # Call 2 with identical inputs (same phone)
    res2, state2 = agent.process_message("Verify my KYC again")
    
    assert res2 == "There was an issue with the verification process. Please try again later."
    assert state2.stage == Stage.END
    assert state2.terminal_state == TerminalState.LOAN_REJECTED


def test_anti_loop_underwriting_agent_direct():
    """
    Directly simulate the flow on MasterAgent's internal handlers to verify the
    anti-loop safeguard for UNDERWRITING_AGENT.
    - First call is allowed.
    - Second call with identical inputs triggers the anti-loop check.
    - MasterAgent should return the specified error message, set Stage.END, and TerminalState.CUSTOMER_DROPPED.
    """
    agent = MasterAgent()
    agent.initialize()
    
    # Setup identical inputs
    agent.state.requested_amount = 300000
    agent.state.tenure_months = 24
    agent.state.preapproved_limit = 500000
    agent.state.interest_rate = 12.5
    agent.state.pan_number = "ABCDE1234F"
    agent.state.salary_slip_received = False
    
    # First invocation
    res1 = agent._handle_underwriting("Evaluate loan request")
    assert "issue processing your application" not in res1
    
    # Re-route stage back to UNDERWRITING, keeping history but clearing terminal state
    agent.state.stage = Stage.UNDERWRITING
    agent.state.terminal_state = None
    
    # Second invocation with identical inputs
    res2 = agent._handle_underwriting("Evaluate loan request again")
    
    assert res2 == "We encountered an issue processing your application. Please try again later."
    assert agent.state.stage == Stage.END
    assert agent.state.terminal_state == TerminalState.CUSTOMER_DROPPED


def test_anti_loop_underwriting_agent_via_process_message():
    """
    Simulate the conversation flow using process_message to verify that
    repeatedly routing to UNDERWRITING_AGENT with same inputs triggers the safeguard.
    """
    agent = MasterAgent()
    agent.initialize()
    
    # Setup identical inputs
    agent.state.requested_amount = 300000
    agent.state.tenure_months = 24
    agent.state.preapproved_limit = 500000
    agent.state.interest_rate = 12.5
    agent.state.pan_number = "ABCDE1234F"
    agent.state.salary_slip_received = False
    
    agent.state.stage = Stage.UNDERWRITING
    
    # Call 1
    res1, state1 = agent.process_message("Evaluate underwriting")
    assert "issue processing your application" not in res1
    
    # Re-route stage back to UNDERWRITING, resetting terminal state
    agent.state.stage = Stage.UNDERWRITING
    agent.state.terminal_state = None
    
    # Call 2
    res2, state2 = agent.process_message("Evaluate underwriting again")
    
    assert res2 == "We encountered an issue processing your application. Please try again later."
    assert state2.stage == Stage.END
    assert state2.terminal_state == TerminalState.CUSTOMER_DROPPED


# =============================================================================
# 2. MAX AGENT CALLS SAFEGUARD TESTS
# =============================================================================

def test_max_agent_calls_safeguard():
    """
    Verify the safeguard that restricts total agent calls.
    - Set total_agent_calls to 6 (the maximum limit).
    - Call process_message("Any message").
    - Verify it returns: "Maximum agent calls exceeded. Conversation ended."
    - Verify stage is Stage.END.
    - Verify terminal_state is TerminalState.CUSTOMER_DROPPED.
    """
    agent = MasterAgent()
    agent.initialize()
    
    # Set the total agent calls to the limit (6)
    agent.state.total_agent_calls = 6
    
    response, state = agent.process_message("Any message")
    
    assert response == "Maximum agent calls exceeded. Conversation ended."
    assert state.stage == Stage.END
    assert state.terminal_state == TerminalState.CUSTOMER_DROPPED


# =============================================================================
# 3. PDF GENERATION VERIFICATION TESTS
# =============================================================================

def test_sanction_agent_pdf_generation():
    """
    Verify the PDF generation capability of SanctionAgent.
    - Initialize SanctionAgent.
    - Process mock loan inputs.
    - If FPDF_AVAILABLE is True, assert that the PDF exists on the filesystem,
      has a non-zero size (is non-empty), and is cleaned up afterward.
    """
    agent = SanctionAgent()
    
    mock_inputs = {
        "customer_name": "Test User",
        "customer_id": "CUST999",
        "approved_amount": 150000.0,
        "tenure_months": 12,
        "interest_rate": 14.5,
        "emi": 13500.0
    }
    
    result = agent.process(mock_inputs)
    
    # Every execution path generates a sanction ID
    assert result["sanction_id"].startswith("POLARIS-")
    
    if FPDF_AVAILABLE:
        assert result["pdf_generated"] is True
        pdf_path = result["pdf_path"]
        assert pdf_path is not None
        
        # Verify file is created and exists
        assert os.path.exists(pdf_path) is True
        
        # Verify the PDF is non-empty
        assert os.path.getsize(pdf_path) > 0, f"PDF file at {pdf_path} is empty."
        
        # Clean up the PDF file
        os.remove(pdf_path)
        
        # Verify file was cleaned up successfully
        assert os.path.exists(pdf_path) is False
    else:
        # Fallback path if FPDF is not installed
        assert result["pdf_generated"] is False
        assert result["pdf_path"] is None
        assert "details" in result
        assert result["details"]["customer_name"] == "Test User"
