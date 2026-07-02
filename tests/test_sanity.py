"""
test_sanity.py - Sanity tests for the POLARIS conversational loan agent.
Verifies MasterAgent imports, state transitions, and LLM mocking.
"""

import os
import sys
from state import Stage, TerminalState
from master_agent import MasterAgent

def test_google_api_key_env_set():
    """Verify that GOOGLE_API_KEY environment variable is set."""
    assert os.environ.get("GOOGLE_API_KEY") == "mock_api_key_for_testing"

def test_master_agent_instantiation():
    """Verify MasterAgent can be instantiated and the model is mocked."""
    agent = MasterAgent()
    assert agent.model is not None
    # Verify it is using our mock class
    assert agent.model.__class__.__name__ == "MockGenerativeModel"

def test_master_agent_basic_greeting():
    """Verify basic message processing (greeting) works and transitions stage."""
    agent = MasterAgent()
    
    # 1. Start conversation with greeting
    response, state = agent.process_message("Hello there")
    
    assert response is not None
    assert "mobile number" in response.lower()
    assert state.stage == Stage.NEED_DISCOVERY
    assert state.customer_phone is None

def test_master_agent_full_approval_flow():
    """Verify full end-to-end loan flow simulation with LLM mocking."""
    agent = MasterAgent()
    
    # Step 1: Initial Greeting
    response, state = agent.process_message("Hi")
    assert state.stage == Stage.NEED_DISCOVERY
    
    # Step 2: Share mobile number (Rahul Sharma: 9876543210)
    response, state = agent.process_message("My phone number is 9876543210")
    assert state.customer_phone == "9876543210"
    assert state.customer_name == "Rahul Sharma"
    assert state.preapproved_limit == 500000.0
    assert state.stage == Stage.OFFER_PRESENTATION
    assert "pre-approved" in response.lower()
    
    # Step 3: Request an amount within the limit (₹300,000 for 24 months)
    # This step invokes SalesAgent, which calls our mocked LLM.
    response, state = agent.process_message("I'd like to get 300000 for 24 months")
    
    # The agent should call SalesAgent, get the mock response, verify KYC,
    # run underwriting, approve, and generate a sanction letter automatically.
    assert state.requested_amount == 300000.0
    assert state.tenure_months == 24
    assert state.kyc_verified is True
    assert state.credit_score == 780
    assert state.terminal_state == TerminalState.LOAN_SANCTIONED
    assert state.stage == Stage.END
    assert "approved" in response.lower() or "congratulations" in response.lower()
    assert state.sanction_id is not None
    assert state.sanction_id.startswith("POLARIS-")
