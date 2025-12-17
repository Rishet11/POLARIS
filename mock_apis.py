"""
POLARIS Mock APIs
Simulates external services: CRM Server and Credit Bureau API.
Designed for easy replacement with real APIs.
"""

import random
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass


# =============================================================================
# MOCK CRM SERVER API
# =============================================================================

@dataclass
class CRMCustomerRecord:
    """Customer record from CRM system."""
    customer_id: str
    full_name: str
    phone: str
    email: str
    address: str
    city: str
    state: str
    pincode: str
    pan_number: str
    aadhar_last_four: str
    kyc_verified: bool
    kyc_verification_date: Optional[str]
    employer: Optional[str]
    monthly_income: Optional[float]
    account_status: str  # ACTIVE, INACTIVE, BLOCKED


# Mock CRM Database
_CRM_DATABASE: Dict[str, CRMCustomerRecord] = {
    "9876543210": CRMCustomerRecord(
        customer_id="CUST001",
        full_name="Rahul Sharma",
        phone="9876543210",
        email="rahul.sharma@email.com",
        address="123, Green Park Colony",
        city="New Delhi",
        state="Delhi",
        pincode="110016",
        pan_number="ABCDE1234F",
        aadhar_last_four="5678",
        kyc_verified=True,
        kyc_verification_date="2024-06-15",
        employer="TCS",
        monthly_income=85000.0,
        account_status="ACTIVE"
    ),
    "9876543211": CRMCustomerRecord(
        customer_id="CUST002",
        full_name="Priya Patel",
        phone="9876543211",
        email="priya.patel@email.com",
        address="456, Sunrise Apartments",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
        pan_number="FGHIJ5678K",
        aadhar_last_four="1234",
        kyc_verified=True,
        kyc_verification_date="2024-08-20",
        employer="Infosys",
        monthly_income=120000.0,
        account_status="ACTIVE"
    ),
    "9876543212": CRMCustomerRecord(
        customer_id="CUST003",
        full_name="Amit Kumar",
        phone="9876543212",
        email="amit.kumar@email.com",
        address="789, Tech Park Road",
        city="Bangalore",
        state="Karnataka",
        pincode="560001",
        pan_number="KLMNO9012P",
        aadhar_last_four="9012",
        kyc_verified=True,
        kyc_verification_date="2024-07-10",
        employer="Wipro",
        monthly_income=65000.0,
        account_status="ACTIVE"
    ),
    "9876543213": CRMCustomerRecord(
        customer_id="CUST004",
        full_name="Vikram Singh",
        phone="9876543213",
        email="vikram.singh@email.com",
        address="321, Industrial Area",
        city="Pune",
        state="Maharashtra",
        pincode="411001",
        pan_number="PQRST3456Q",
        aadhar_last_four="3456",
        kyc_verified=True,
        kyc_verification_date="2024-05-05",
        employer="Self-employed",
        monthly_income=45000.0,
        account_status="ACTIVE"
    ),
    "9876543214": CRMCustomerRecord(
        customer_id="CUST005",
        full_name="Sneha Reddy",
        phone="9876543214",
        email="sneha.reddy@email.com",
        address="555, Lake View Villas",
        city="Hyderabad",
        state="Telangana",
        pincode="500001",
        pan_number="UVWXY7890R",
        aadhar_last_four="7890",
        kyc_verified=False,  # KYC NOT VERIFIED
        kyc_verification_date=None,
        employer="Amazon",
        monthly_income=95000.0,
        account_status="ACTIVE"
    ),
}


class CRMServerAPI:
    """
    Mock CRM Server API.
    Simulates calls to customer relationship management system.
    """
    
    BASE_URL = "https://api.polaris-crm.internal/v1"
    
    @staticmethod
    def fetch_customer(phone: str) -> Dict[str, Any]:
        """
        GET /customers/lookup?phone={phone}
        Fetches customer details from CRM.
        """
        # Simulate API latency
        time.sleep(0.1)
        
        # Normalize phone
        phone = phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("+91"):
            phone = phone[3:]
        if phone.startswith("91") and len(phone) == 12:
            phone = phone[2:]
        
        customer = _CRM_DATABASE.get(phone)
        
        if not customer:
            return {
                "success": False,
                "error_code": "CUSTOMER_NOT_FOUND",
                "error_message": "No customer record found for this phone number",
                "data": None
            }
        
        return {
            "success": True,
            "error_code": None,
            "error_message": None,
            "data": {
                "customer_id": customer.customer_id,
                "full_name": customer.full_name,
                "phone": customer.phone,
                "email": customer.email,
                "address": {
                    "line1": customer.address,
                    "city": customer.city,
                    "state": customer.state,
                    "pincode": customer.pincode
                },
                "identity": {
                    "pan_number": customer.pan_number,
                    "aadhar_last_four": customer.aadhar_last_four
                },
                "kyc_status": {
                    "verified": customer.kyc_verified,
                    "verification_date": customer.kyc_verification_date
                },
                "employment": {
                    "employer": customer.employer,
                    "monthly_income": customer.monthly_income
                },
                "account_status": customer.account_status
            }
        }
    
    @staticmethod
    def verify_kyc(customer_id: str, pan: str, aadhar_last_four: str) -> Dict[str, Any]:
        """
        POST /customers/{customer_id}/verify-kyc
        Verifies KYC documents.
        """
        time.sleep(0.1)
        
        # Find customer
        for customer in _CRM_DATABASE.values():
            if customer.customer_id == customer_id:
                # Check if documents match
                if customer.pan_number == pan and customer.aadhar_last_four == aadhar_last_four:
                    return {
                        "success": True,
                        "verified": True,
                        "message": "KYC verification successful"
                    }
                else:
                    return {
                        "success": True,
                        "verified": False,
                        "message": "Document mismatch"
                    }
        
        return {
            "success": False,
            "error_code": "CUSTOMER_NOT_FOUND",
            "message": "Customer not found"
        }


# =============================================================================
# MOCK CREDIT BUREAU API
# =============================================================================

@dataclass
class CreditBureauRecord:
    """Credit record from bureau."""
    pan_number: str
    credit_score: int  # Out of 900
    active_loans: int
    total_outstanding: float
    payment_history_score: int  # 0-100
    credit_utilization: float  # 0-100%
    oldest_account_age_months: int
    recent_inquiries: int
    delinquent_accounts: int


# Mock Credit Bureau Database
_CREDIT_BUREAU_DATABASE: Dict[str, CreditBureauRecord] = {
    "ABCDE1234F": CreditBureauRecord(  # Rahul Sharma
        pan_number="ABCDE1234F",
        credit_score=780,
        active_loans=1,
        total_outstanding=250000.0,
        payment_history_score=95,
        credit_utilization=25.0,
        oldest_account_age_months=84,
        recent_inquiries=2,
        delinquent_accounts=0
    ),
    "FGHIJ5678K": CreditBureauRecord(  # Priya Patel
        pan_number="FGHIJ5678K",
        credit_score=820,
        active_loans=0,
        total_outstanding=0.0,
        payment_history_score=100,
        credit_utilization=15.0,
        oldest_account_age_months=120,
        recent_inquiries=1,
        delinquent_accounts=0
    ),
    "KLMNO9012P": CreditBureauRecord(  # Amit Kumar
        pan_number="KLMNO9012P",
        credit_score=750,
        active_loans=2,
        total_outstanding=180000.0,
        payment_history_score=88,
        credit_utilization=40.0,
        oldest_account_age_months=60,
        recent_inquiries=3,
        delinquent_accounts=0
    ),
    "PQRST3456Q": CreditBureauRecord(  # Vikram Singh - LOW SCORE
        pan_number="PQRST3456Q",
        credit_score=650,  # Below threshold
        active_loans=4,
        total_outstanding=450000.0,
        payment_history_score=55,
        credit_utilization=85.0,
        oldest_account_age_months=36,
        recent_inquiries=8,
        delinquent_accounts=2
    ),
    "UVWXY7890R": CreditBureauRecord(  # Sneha Reddy
        pan_number="UVWXY7890R",
        credit_score=760,
        active_loans=1,
        total_outstanding=100000.0,
        payment_history_score=92,
        credit_utilization=20.0,
        oldest_account_age_months=48,
        recent_inquiries=2,
        delinquent_accounts=0
    ),
}


class CreditBureauAPI:
    """
    Mock Credit Bureau API.
    Simulates calls to external credit bureau (like CIBIL/Experian).
    """
    
    BASE_URL = "https://api.credit-bureau.external/v2"
    
    @staticmethod
    def fetch_credit_score(pan_number: str) -> Dict[str, Any]:
        """
        POST /credit-report/fetch
        Fetches credit score and report from bureau.
        """
        # Simulate API latency
        time.sleep(0.15)
        
        record = _CREDIT_BUREAU_DATABASE.get(pan_number.upper())
        
        if not record:
            return {
                "success": False,
                "error_code": "PAN_NOT_FOUND",
                "error_message": "No credit history found for this PAN",
                "data": None
            }
        
        return {
            "success": True,
            "error_code": None,
            "error_message": None,
            "data": {
                "pan_number": record.pan_number,
                "credit_score": record.credit_score,
                "score_range": {
                    "min": 300,
                    "max": 900
                },
                "score_rating": _get_score_rating(record.credit_score),
                "credit_summary": {
                    "active_loans": record.active_loans,
                    "total_outstanding": record.total_outstanding,
                    "payment_history_score": record.payment_history_score,
                    "credit_utilization_percent": record.credit_utilization,
                    "oldest_account_age_months": record.oldest_account_age_months,
                    "recent_inquiries_90_days": record.recent_inquiries,
                    "delinquent_accounts": record.delinquent_accounts
                },
                "report_generated_at": "2024-12-17T16:00:00Z"
            }
        }


def _get_score_rating(score: int) -> str:
    """Get rating based on credit score."""
    if score >= 800:
        return "EXCELLENT"
    elif score >= 750:
        return "GOOD"
    elif score >= 700:
        return "FAIR"
    elif score >= 650:
        return "POOR"
    else:
        return "VERY_POOR"


# =============================================================================
# OFFER MART API (Pre-approved limits)
# =============================================================================

@dataclass
class PreApprovedOffer:
    """Pre-approved loan offer."""
    customer_id: str
    preapproved_limit: float
    interest_rate: float
    max_tenure_months: int
    offer_valid_until: str
    offer_type: str


_OFFER_DATABASE: Dict[str, PreApprovedOffer] = {
    "CUST001": PreApprovedOffer(
        customer_id="CUST001",
        preapproved_limit=500000.0,
        interest_rate=12.5,
        max_tenure_months=60,
        offer_valid_until="2025-03-31",
        offer_type="PREMIUM"
    ),
    "CUST002": PreApprovedOffer(
        customer_id="CUST002",
        preapproved_limit=750000.0,
        interest_rate=11.0,
        max_tenure_months=72,
        offer_valid_until="2025-03-31",
        offer_type="SUPER_PREMIUM"
    ),
    "CUST003": PreApprovedOffer(
        customer_id="CUST003",
        preapproved_limit=300000.0,
        interest_rate=13.5,
        max_tenure_months=48,
        offer_valid_until="2025-02-28",
        offer_type="STANDARD"
    ),
    "CUST004": PreApprovedOffer(  # Low credit - no offer
        customer_id="CUST004",
        preapproved_limit=0.0,
        interest_rate=18.0,
        max_tenure_months=24,
        offer_valid_until="2025-01-31",
        offer_type="NONE"
    ),
    "CUST005": PreApprovedOffer(
        customer_id="CUST005",
        preapproved_limit=400000.0,
        interest_rate=12.0,
        max_tenure_months=48,
        offer_valid_until="2025-03-31",
        offer_type="STANDARD"
    ),
}


class OfferMartAPI:
    """
    Offer Mart API - Internal service for pre-approved offers.
    """
    
    BASE_URL = "https://api.polaris-offers.internal/v1"
    
    @staticmethod
    def get_preapproved_offer(customer_id: str) -> Dict[str, Any]:
        """
        GET /offers/preapproved/{customer_id}
        Fetches pre-approved offer for customer.
        """
        time.sleep(0.05)
        
        offer = _OFFER_DATABASE.get(customer_id)
        
        if not offer or offer.offer_type == "NONE":
            return {
                "success": False,
                "error_code": "NO_OFFER_AVAILABLE",
                "error_message": "No pre-approved offer available for this customer",
                "data": None
            }
        
        return {
            "success": True,
            "error_code": None,
            "error_message": None,
            "data": {
                "customer_id": offer.customer_id,
                "preapproved_limit": offer.preapproved_limit,
                "interest_rate_percent": offer.interest_rate,
                "max_tenure_months": offer.max_tenure_months,
                "offer_valid_until": offer.offer_valid_until,
                "offer_type": offer.offer_type
            }
        }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """
    Calculate EMI using reducing balance method.
    
    Args:
        principal: Loan amount
        annual_rate: Annual interest rate (percentage)
        tenure_months: Loan tenure in months
    
    Returns:
        Monthly EMI amount
    """
    monthly_rate = annual_rate / 12 / 100
    
    if monthly_rate == 0:
        return principal / tenure_months
    
    emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure_months) / (((1 + monthly_rate) ** tenure_months) - 1)
    return round(emi, 2)
