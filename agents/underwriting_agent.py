"""
POLARIS Underwriting Agent
Handles credit decision based on defined rules.
"""

from typing import Any, Dict
from .base_agent import BaseAgent
from offer_mart import calculate_emi


class UnderwritingAgent(BaseAgent):
    """
    Underwriting Agent for credit decisions.
    
    Input: {requested_amount, tenure_months, preapproved_limit, credit_score, salary (optional)}
    Output: {decision: APPROVED|REJECTED|NEED_SALARY_SLIP, emi, reason}
    
    Rules:
    - Reject if credit_score < 700
    - Approve instantly if amount ≤ preapproved_limit
    - If amount ≤ 2× limit → require salary slip
    - Reject if amount > 2× limit
    """
    
    # Credit score threshold
    MIN_CREDIT_SCORE = 700
    
    # Interest rate for EMI calculation (use customer's rate if available)
    DEFAULT_INTEREST_RATE = 14.0
    
    def __init__(self):
        super().__init__("UNDERWRITING_AGENT")
    
    def get_system_prompt(self) -> str:
        # Not used as this agent uses rule-based logic
        return ""
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make underwriting decision based on rules.
        
        Args:
            inputs: {
                requested_amount: float,
                tenure_months: int,
                preapproved_limit: float,
                credit_score: int,
                interest_rate: float (optional),
                salary: float (optional)
            }
        
        Returns:
            {decision, emi, reason, approved_amount (if approved)}
        """
        requested_amount = inputs.get("requested_amount", 0)
        tenure_months = inputs.get("tenure_months", 12)
        preapproved_limit = inputs.get("preapproved_limit", 0)
        credit_score = inputs.get("credit_score", 0)
        interest_rate = inputs.get("interest_rate", self.DEFAULT_INTEREST_RATE)
        salary = inputs.get("salary")
        
        # Validate inputs
        if not requested_amount or requested_amount <= 0:
            return {
                "decision": "REJECTED",
                "emi": None,
                "reason": "Invalid loan amount requested",
                "approved_amount": None
            }
        
        if not tenure_months or tenure_months <= 0:
            tenure_months = 12  # Default to 12 months
        
        # RULE 1: Reject if credit score < 700
        if credit_score < self.MIN_CREDIT_SCORE:
            return {
                "decision": "REJECTED",
                "emi": None,
                "reason": f"Credit score ({credit_score}) is below minimum requirement ({self.MIN_CREDIT_SCORE})",
                "approved_amount": None
            }
        
        # Calculate EMI for the requested amount
        emi = calculate_emi(requested_amount, interest_rate, tenure_months)
        
        # RULE 2: Approve if amount ≤ preapproved limit
        if requested_amount <= preapproved_limit:
            return {
                "decision": "APPROVED",
                "emi": emi,
                "reason": f"Loan approved within preapproved limit of ₹{preapproved_limit:,.0f}",
                "approved_amount": requested_amount,
                "interest_rate": interest_rate,
                "tenure_months": tenure_months
            }
        
        # Calculate 2x limit threshold
        double_limit = preapproved_limit * 2
        
        # RULE 3: If amount ≤ 2× limit, require salary slip
        if requested_amount <= double_limit:
            if salary and salary > 0:
                # Salary slip provided - check affordability
                max_emi_allowed = salary * 0.5  # 50% of salary as EMI limit
                if emi <= max_emi_allowed:
                    return {
                        "decision": "APPROVED",
                        "emi": emi,
                        "reason": f"Loan approved after salary verification. Monthly salary: ₹{salary:,.0f}, EMI: ₹{emi:,.0f}",
                        "approved_amount": requested_amount,
                        "interest_rate": interest_rate,
                        "tenure_months": tenure_months
                    }
                else:
                    return {
                        "decision": "REJECTED",
                        "emi": emi,
                        "reason": f"EMI (₹{emi:,.0f}) exceeds 50% of monthly salary (₹{salary:,.0f}). Maximum affordable loan is lower.",
                        "approved_amount": None
                    }
            else:
                # Salary slip not provided yet
                return {
                    "decision": "NEED_SALARY_SLIP",
                    "emi": emi,
                    "reason": f"Requested amount (₹{requested_amount:,.0f}) exceeds preapproved limit (₹{preapproved_limit:,.0f}). Salary verification required.",
                    "approved_amount": None
                }
        
        # RULE 4: Reject if amount > 2× limit
        return {
            "decision": "REJECTED",
            "emi": None,
            "reason": f"Requested amount (₹{requested_amount:,.0f}) exceeds maximum eligible limit (₹{double_limit:,.0f})",
            "approved_amount": None
        }
