"""
POLARIS Verification Agent
Handles KYC verification against Offer Mart.
"""

from typing import Any, Dict
from .base_agent import BaseAgent
from offer_mart import lookup_customer_by_phone, lookup_customer_by_id


class VerificationAgent(BaseAgent):
    """
    Verification Agent for KYC verification.
    
    Input: Customer phone or ID
    Output: {kyc_verified, customer_profile}
    
    Rules:
    - Verify against Offer Mart database
    - Return full customer profile if verified
    - No LLM calls needed (pure database lookup)
    """
    
    def __init__(self):
        super().__init__("VERIFICATION_AGENT")
    
    def get_system_prompt(self) -> str:
        # Not used as this agent doesn't need LLM
        return ""
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify customer KYC status.
        
        Args:
            inputs: {"phone": str} or {"customer_id": str}
        
        Returns:
            {kyc_verified: bool, customer_profile: dict or None, error: str (if any)}
        """
        phone = inputs.get("phone")
        customer_id = inputs.get("customer_id")
        
        # Look up customer
        customer = None
        if phone:
            customer = lookup_customer_by_phone(phone)
        elif customer_id:
            customer = lookup_customer_by_id(customer_id)
        
        if not customer:
            return {
                "kyc_verified": False,
                "customer_profile": None,
                "error": "Customer not found in our records"
            }
        
        # Check KYC status
        if not customer.kyc_verified:
            return {
                "kyc_verified": False,
                "customer_profile": {
                    "customer_id": customer.customer_id,
                    "name": customer.name,
                    "phone": customer.phone,
                },
                "error": "KYC verification pending. Please complete KYC first."
            }
        
        # Return full verified profile
        return {
            "kyc_verified": True,
            "customer_profile": {
                "customer_id": customer.customer_id,
                "name": customer.name,
                "phone": customer.phone,
                "email": customer.email,
                "credit_score": customer.credit_score,
                "preapproved_limit": customer.preapproved_limit,
                "interest_rate": customer.interest_rate,
                "max_tenure_months": customer.max_tenure_months,
                "employer": customer.employer,
                "monthly_salary": customer.monthly_salary,
            },
            "error": None
        }
