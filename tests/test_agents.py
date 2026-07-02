"""
tests/test_agents.py - Unit and logic tests for the individual sub-agents:
SalesAgent, VerificationAgent, UnderwritingAgent, and SanctionAgent.
"""

import os
import pytest
from unittest.mock import patch

from agents.sales_agent import SalesAgent
from agents.verification_agent import VerificationAgent
from agents.underwriting_agent import UnderwritingAgent
from agents.sanction_agent import SanctionAgent, FPDF_AVAILABLE


# =============================================================================
# 1. SALES AGENT TESTS
# =============================================================================

def test_sales_agent_process_format():
    """Verify that process() returns a valid dictionary with required fields."""
    agent = SalesAgent()
    inputs = {"customer_message": "Hello, I am interested in a loan."}
    result = agent.process(inputs)
    
    assert isinstance(result, dict)
    assert "sales_pitch" in result
    assert "requested_amount" in result
    assert "tenure_months" in result
    assert "purpose" in result


def test_sales_agent_data_extraction():
    """Test mock LLM data extraction (e.g., requesting 300k for 24 months)."""
    agent = SalesAgent()
    inputs = {"customer_message": "I would like to request 300000 for 24 months"}
    result = agent.process(inputs)
    
    assert result["requested_amount"] == 300000
    assert result["tenure_months"] == 24
    assert result["purpose"] == "wedding"


# =============================================================================
# 2. VERIFICATION AGENT TESTS
# =============================================================================

def test_verification_agent_verified_kyc():
    """Query CRM lookup successfully for verified KYC (e.g., Rahul Sharma 9876543210)."""
    agent = VerificationAgent()
    inputs = {"phone": "9876543210"}
    result = agent.process(inputs)
    
    assert result["kyc_verified"] is True
    assert result["error"] is None
    
    profile = result["customer_profile"]
    assert profile is not None
    assert profile["customer_id"] == "CUST001"
    assert profile["name"] == "Rahul Sharma"
    assert profile["phone"] == "9876543210"
    assert profile["email"] == "rahul.sharma@email.com"
    assert "New Delhi" in profile["address"]
    assert profile["employer"] == "TCS"
    assert profile["monthly_salary"] == 85000.0
    assert profile["pan_number"] == "ABCDE1234F"
    assert profile["kyc_verified"] is True
    assert profile["kyc_verification_date"] == "2024-06-15"
    
    offer = result["preapproved_offer"]
    assert offer is not None
    assert offer["customer_id"] == "CUST001"
    assert offer["preapproved_limit"] == 500000.0
    assert offer["interest_rate_percent"] == 12.5
    assert offer["max_tenure_months"] == 60


def test_verification_agent_unverified_kyc():
    """Query CRM lookup for unverified KYC (e.g., Sneha Reddy 9876543214)."""
    agent = VerificationAgent()
    inputs = {"phone": "9876543214"}
    result = agent.process(inputs)
    
    assert result["kyc_verified"] is False
    assert result["preapproved_offer"] is None
    assert result["error"] == "KYC verification pending. Please complete KYC first."
    
    profile = result["customer_profile"]
    assert profile is not None
    assert profile["customer_id"] == "CUST005"
    assert profile["name"] == "Sneha Reddy"
    assert profile["phone"] == "9876543214"


def test_verification_agent_non_existent():
    """Query CRM lookup for non-existent customer and return clean failure dict."""
    agent = VerificationAgent()
    inputs = {"phone": "9999999999"}
    result = agent.process(inputs)
    
    assert result["kyc_verified"] is False
    assert result["customer_profile"] is None
    assert result["preapproved_offer"] is None
    assert result["error"] == "No customer record found for this phone number"
    assert result["crm_response"] is not None
    assert result["crm_response"]["success"] is False


# =============================================================================
# 3. UNDERWRITING AGENT TESTS
# =============================================================================

def test_underwriting_agent_low_credit_score():
    """Rule: Reject if credit score < 700 (e.g. Vikram Singh 9876543213)."""
    agent = UnderwritingAgent()
    inputs = {
        "requested_amount": 100000,
        "tenure_months": 12,
        "preapproved_limit": 0,
        "interest_rate": 14.0,
        "pan_number": "PQRST3456Q"  # Vikram Singh: Credit score 650
    }
    result = agent.process(inputs)
    
    assert result["decision"] == "REJECTED"
    assert result["approved_amount"] is None
    assert "Credit score (650/900) is below minimum requirement" in result["reason"]


def test_underwriting_agent_approve_instantly():
    """Rule: Approve instantly if requested amount <= preapproved limit (Rahul Sharma)."""
    agent = UnderwritingAgent()
    inputs = {
        "requested_amount": 300000,
        "tenure_months": 24,
        "preapproved_limit": 500000,
        "interest_rate": 12.5,
        "pan_number": "ABCDE1234F"  # Rahul Sharma: Credit score 780
    }
    result = agent.process(inputs)
    
    assert result["decision"] == "APPROVED"
    assert result["approved_amount"] == 300000
    assert result["emi"] is not None
    assert "approved within preapproved limit" in result["reason"].lower()


def test_underwriting_agent_need_salary_slip():
    """Rule: Set decision to NEED_SALARY_SLIP if amount is between limit and 2x limit without salary."""
    agent = UnderwritingAgent()
    inputs = {
        "requested_amount": 600000,  # > 500k limit and <= 1000k (2x limit)
        "tenure_months": 24,
        "preapproved_limit": 500000,
        "interest_rate": 12.5,
        "pan_number": "ABCDE1234F",
        "salary": None
    }
    result = agent.process(inputs)
    
    assert result["decision"] == "NEED_SALARY_SLIP"
    assert result["approved_amount"] is None
    assert "income verification required" in result["reason"].lower()


def test_underwriting_agent_approve_with_salary():
    """Rule: Approve after income verification if EMI <= 50% salary."""
    agent = UnderwritingAgent()
    inputs = {
        "requested_amount": 600000,
        "tenure_months": 24,
        "preapproved_limit": 500000,
        "interest_rate": 12.5,
        "pan_number": "ABCDE1234F",
        "salary": 85000.0  # EMI (~28,383) <= 42,500 (50% of 85,000)
    }
    result = agent.process(inputs)
    
    assert result["decision"] == "APPROVED"
    assert result["approved_amount"] == 600000
    assert "approved after income verification" in result["reason"].lower()


def test_underwriting_agent_reject_due_to_salary():
    """Rule: Reject after income verification if EMI > 50% salary."""
    agent = UnderwritingAgent()
    inputs = {
        "requested_amount": 600000,
        "tenure_months": 24,
        "preapproved_limit": 500000,
        "interest_rate": 12.5,
        "pan_number": "ABCDE1234F",
        "salary": 10000.0  # EMI (~28,383) > 5,000 (50% of 10,000)
    }
    result = agent.process(inputs)
    
    assert result["decision"] == "REJECTED"
    assert result["approved_amount"] is None
    assert "exceeds 50% of monthly salary" in result["reason"].lower()


def test_underwriting_agent_reject_above_double_limit():
    """Rule: Reject if requested amount > 2x limit (e.g. 1.2M vs 500k limit)."""
    agent = UnderwritingAgent()
    inputs = {
        "requested_amount": 1200000,  # > 1,000,000 (2x limit)
        "tenure_months": 24,
        "preapproved_limit": 500000,
        "interest_rate": 12.5,
        "pan_number": "ABCDE1234F"
    }
    result = agent.process(inputs)
    
    assert result["decision"] == "REJECTED"
    assert result["approved_amount"] is None
    assert "exceeds maximum eligible limit" in result["reason"].lower()


# =============================================================================
# 4. SANCTION AGENT TESTS
# =============================================================================

def test_sanction_agent_sanction_id_generation():
    """Verify that calling process() generates a unique sanction ID starting with POLARIS-."""
    agent = SanctionAgent()
    inputs = {
        "customer_name": "Rahul Sharma",
        "customer_id": "CUST001",
        "approved_amount": 300000,
        "tenure_months": 24,
        "interest_rate": 12.5,
        "emi": 14191.0
    }
    
    result_1 = agent.process(inputs)
    result_2 = agent.process(inputs)
    
    assert result_1["sanction_id"].startswith("POLARIS-")
    assert result_2["sanction_id"].startswith("POLARIS-")
    assert result_1["sanction_id"] != result_2["sanction_id"]


def test_sanction_agent_fpdf_flow():
    """
    Verify SanctionAgent behavior depending on FPDF_AVAILABLE.
    If True, verifies PDF generation, field, and clean-up.
    If False, verifies mock response.
    """
    agent = SanctionAgent()
    inputs = {
        "customer_name": "Rahul Sharma",
        "customer_id": "CUST001",
        "approved_amount": 300000,
        "tenure_months": 24,
        "interest_rate": 12.5,
        "emi": 14191.0
    }
    
    # Test path 1: Actual execution based on the module's real FPDF_AVAILABLE value
    result = agent.process(inputs)
    assert result["sanction_id"].startswith("POLARIS-")
    
    if FPDF_AVAILABLE:
        assert result["pdf_generated"] is True
        pdf_path = result["pdf_path"]
        assert pdf_path is not None
        assert os.path.exists(pdf_path)
        
        # Cleanup
        os.remove(pdf_path)
        assert not os.path.exists(pdf_path)
    else:
        assert result["pdf_generated"] is False
        assert result["pdf_path"] is None
        assert "details" in result
        assert result["details"]["customer_name"] == "Rahul Sharma"


def test_sanction_agent_fpdf_disabled_explicit():
    """Explicitly verify the FPDF_AVAILABLE = False code path via mocking."""
    with patch("agents.sanction_agent.FPDF_AVAILABLE", False):
        agent = SanctionAgent()
        inputs = {
            "customer_name": "Rahul Sharma",
            "customer_id": "CUST001",
            "approved_amount": 300000,
            "tenure_months": 24,
            "interest_rate": 12.5,
            "emi": 14191.0
        }
        result = agent.process(inputs)
        assert result["pdf_generated"] is False
        assert result["pdf_path"] is None
        assert result["sanction_id"].startswith("POLARIS-")
        assert "details" in result
        assert result["details"]["customer_name"] == "Rahul Sharma"
        assert result["details"]["approved_amount"] == 300000
