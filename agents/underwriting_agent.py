"""
POLARIS Underwriting Agent
Fetches credit score from Credit Bureau and validates eligibility.
"""

from typing import Any, Dict
from .base_agent import BaseAgent
from mock_apis import CreditBureauAPI, calculate_emi


class UnderwritingAgent(BaseAgent):
    """
    Underwriting Agent for credit decisions.
    
    Responsibilities:
    - Fetch credit score from Credit Bureau API
    - Validate eligibility based on rules
    - Calculate EMI and affordability
    
    Rules:
    - Reject if credit_score < 700
    - Approve instantly if amount ≤ preapproved_limit
    - If amount ≤ 2× limit → require salary slip, approve if EMI ≤ 50% salary
    - Reject if amount > 2× limit
    
    Input: {requested_amount, tenure_months, preapproved_limit, pan_number, salary (optional)}
    Output: {decision: APPROVED|REJECTED|NEED_SALARY_SLIP, emi, reason, credit_report}
    """
    
    # Credit score threshold
    MIN_CREDIT_SCORE = 700
    
    # EMI affordability threshold (50% of salary)
    MAX_EMI_TO_SALARY_RATIO = 0.5
    
    def __init__(self):
        super().__init__("UNDERWRITING_AGENT")
        self.credit_bureau_api = CreditBureauAPI()
    
    def get_system_prompt(self) -> str:
        # Not used as this agent uses rule-based logic
        return ""
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make underwriting decision based on credit bureau data and rules.
        
        Args:
            inputs: {
                requested_amount: float,
                tenure_months: int,
                preapproved_limit: float,
                interest_rate: float,
                pan_number: str,
                salary: float (optional)
            }
        
        Returns:
            {
                decision: APPROVED|REJECTED|NEED_SALARY_SLIP,
                emi: float,
                reason: str,
                approved_amount: float (if approved),
                credit_report: dict (from Credit Bureau)
            }
        """
        requested_amount = inputs.get("requested_amount", 0)
        tenure_months = inputs.get("tenure_months", 12)
        preapproved_limit = inputs.get("preapproved_limit", 0)
        interest_rate = inputs.get("interest_rate", 14.0)
        pan_number = inputs.get("pan_number")
        salary = inputs.get("salary")
        
        # Validate inputs
        if not requested_amount or requested_amount <= 0:
            return {
                "decision": "REJECTED",
                "emi": None,
                "reason": "Invalid loan amount requested",
                "approved_amount": None,
                "credit_report": None
            }
        
        if not tenure_months or tenure_months <= 0:
            tenure_months = 12  # Default to 12 months
        
        # Step 1: Fetch credit score from Credit Bureau
        credit_report = None
        credit_score = 0
        
        if pan_number:
            bureau_response = self.credit_bureau_api.fetch_credit_score(pan_number)
            
            if bureau_response.get("success"):
                credit_report = bureau_response.get("data")
                credit_score = credit_report.get("credit_score", 0)
            else:
                # No credit history found
                return {
                    "decision": "REJECTED",
                    "emi": None,
                    "reason": "Unable to fetch credit score. No credit history found.",
                    "approved_amount": None,
                    "credit_report": None
                }
        else:
            return {
                "decision": "REJECTED",
                "emi": None,
                "reason": "PAN number required for credit check",
                "approved_amount": None,
                "credit_report": None
            }
        
        # RULE 1: Reject if credit score < 700
        if credit_score < self.MIN_CREDIT_SCORE:
            return {
                "decision": "REJECTED",
                "emi": None,
                "reason": f"Credit score ({credit_score}/900) is below minimum requirement ({self.MIN_CREDIT_SCORE})",
                "approved_amount": None,
                "credit_report": credit_report
            }
        
        # Calculate EMI for the requested amount
        emi = calculate_emi(requested_amount, interest_rate, tenure_months)
        
        # RULE 2: Approve if amount ≤ preapproved limit
        if requested_amount <= preapproved_limit:
            return {
                "decision": "APPROVED",
                "emi": emi,
                "reason": f"Loan approved within preapproved limit of ₹{preapproved_limit:,.0f}. Credit score: {credit_score}/900 ({credit_report.get('score_rating', 'N/A')})",
                "approved_amount": requested_amount,
                "interest_rate": interest_rate,
                "tenure_months": tenure_months,
                "credit_report": credit_report
            }
        
        # Calculate 2x limit threshold
        double_limit = preapproved_limit * 2
        
        # RULE 3: If amount ≤ 2× limit, require salary slip
        if requested_amount <= double_limit:
            if salary and salary > 0:
                # Salary slip provided - check affordability
                max_emi_allowed = salary * self.MAX_EMI_TO_SALARY_RATIO
                
                if emi <= max_emi_allowed:
                    return {
                        "decision": "APPROVED",
                        "emi": emi,
                        "reason": f"Loan approved after income verification. Credit score: {credit_score}/900. Monthly salary: ₹{salary:,.0f}, EMI: ₹{emi:,.0f} ({(emi/salary)*100:.1f}% of salary)",
                        "approved_amount": requested_amount,
                        "interest_rate": interest_rate,
                        "tenure_months": tenure_months,
                        "credit_report": credit_report
                    }
                else:
                    # EMI too high compared to salary
                    max_affordable_amount = self._calculate_max_loan(max_emi_allowed, interest_rate, tenure_months)
                    return {
                        "decision": "REJECTED",
                        "emi": emi,
                        "reason": f"EMI (₹{emi:,.0f}) exceeds 50% of monthly salary (₹{salary:,.0f}). Maximum affordable loan is ₹{max_affordable_amount:,.0f}",
                        "approved_amount": None,
                        "credit_report": credit_report,
                        "suggested_amount": max_affordable_amount
                    }
            else:
                # Salary slip not provided yet
                return {
                    "decision": "NEED_SALARY_SLIP",
                    "emi": emi,
                    "reason": f"Requested amount (₹{requested_amount:,.0f}) exceeds preapproved limit (₹{preapproved_limit:,.0f}). Credit score: {credit_score}/900. Income verification required.",
                    "approved_amount": None,
                    "credit_report": credit_report
                }
        
        # RULE 4: Reject if amount > 2× limit
        return {
            "decision": "REJECTED",
            "emi": None,
            "reason": f"Requested amount (₹{requested_amount:,.0f}) exceeds maximum eligible limit (₹{double_limit:,.0f}). Credit score: {credit_score}/900.",
            "approved_amount": None,
            "credit_report": credit_report,
            "max_eligible": double_limit
        }
    
    def _calculate_max_loan(self, max_emi: float, annual_rate: float, tenure_months: int) -> float:
        """Calculate maximum loan amount for given EMI."""
        monthly_rate = annual_rate / 12 / 100
        if monthly_rate == 0:
            return max_emi * tenure_months
        
        principal = max_emi * (((1 + monthly_rate) ** tenure_months) - 1) / (monthly_rate * ((1 + monthly_rate) ** tenure_months))
        return round(principal, 0)
