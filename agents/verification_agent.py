"""
POLARIS Verification Agent
Confirms KYC details from the CRM Server.
"""

from typing import Any, Dict
from .base_agent import BaseAgent
from mock_apis import CRMServerAPI, OfferMartAPI


class VerificationAgent(BaseAgent):
    """
    Verification Agent for KYC verification.
    
    Responsibilities:
    - Fetch customer details from CRM Server
    - Verify KYC status
    - Retrieve pre-approved offer from Offer Mart
    
    Input: Customer phone or ID
    Output: {kyc_verified, customer_profile, preapproved_offer}
    """
    
    def __init__(self):
        super().__init__("VERIFICATION_AGENT")
        self.crm_api = CRMServerAPI()
        self.offer_api = OfferMartAPI()
    
    def get_system_prompt(self) -> str:
        # Not used as this agent doesn't need LLM
        return ""
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify customer KYC status from CRM Server.
        
        Args:
            inputs: {"phone": str} or {"customer_id": str}
        
        Returns:
            {
                kyc_verified: bool,
                customer_profile: dict or None,
                preapproved_offer: dict or None,
                crm_response: dict,  # Raw API response
                error: str (if any)
            }
        """
        phone = inputs.get("phone")
        customer_id = inputs.get("customer_id")
        
        # Step 1: Fetch customer from CRM
        if phone:
            crm_response = self.crm_api.fetch_customer(phone)
        else:
            return {
                "kyc_verified": False,
                "customer_profile": None,
                "preapproved_offer": None,
                "crm_response": None,
                "error": "Phone number is required"
            }
        
        # Check CRM response
        if not crm_response.get("success"):
            return {
                "kyc_verified": False,
                "customer_profile": None,
                "preapproved_offer": None,
                "crm_response": crm_response,
                "error": crm_response.get("error_message", "Customer not found in CRM")
            }
        
        customer_data = crm_response.get("data", {})
        
        # Step 2: Check KYC status
        kyc_status = customer_data.get("kyc_status", {})
        if not kyc_status.get("verified"):
            return {
                "kyc_verified": False,
                "customer_profile": {
                    "customer_id": customer_data.get("customer_id"),
                    "name": customer_data.get("full_name"),
                    "phone": customer_data.get("phone"),
                },
                "preapproved_offer": None,
                "crm_response": crm_response,
                "error": "KYC verification pending. Please complete KYC first."
            }
        
        # Step 3: Fetch pre-approved offer
        customer_id = customer_data.get("customer_id")
        offer_response = self.offer_api.get_preapproved_offer(customer_id)
        
        preapproved_offer = None
        if offer_response.get("success"):
            preapproved_offer = offer_response.get("data")
        
        # Build customer profile
        employment = customer_data.get("employment", {})
        address = customer_data.get("address", {})
        
        customer_profile = {
            "customer_id": customer_data.get("customer_id"),
            "name": customer_data.get("full_name"),
            "phone": customer_data.get("phone"),
            "email": customer_data.get("email"),
            "address": f"{address.get('line1')}, {address.get('city')}, {address.get('state')} - {address.get('pincode')}",
            "employer": employment.get("employer"),
            "monthly_salary": employment.get("monthly_income"),
            "pan_number": customer_data.get("identity", {}).get("pan_number"),
            "kyc_verified": True,
            "kyc_verification_date": kyc_status.get("verification_date"),
        }
        
        return {
            "kyc_verified": True,
            "customer_profile": customer_profile,
            "preapproved_offer": preapproved_offer,
            "crm_response": crm_response,
            "error": None
        }
