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
    # NEW CUSTOMERS (6-10)
    "9876543215": CRMCustomerRecord(
        customer_id="CUST006",
        full_name="Arjun Das",
        phone="9876543215",
        email="arjun.das@email.com",
        address="101, Sector 15",
        city="Noida",
        state="Uttar Pradesh",
        pincode="201301",
        pan_number="DASAJ1234A",
        aadhar_last_four="1111",
        kyc_verified=True,
        kyc_verification_date="2024-09-01",
        employer="Swiggy",
        monthly_income=35000.0,
        account_status="ACTIVE"
    ),
    "9876543216": CRMCustomerRecord(
        customer_id="CUST007",
        full_name="Meera Iyer",
        phone="9876543216",
        email="meera.iyer@email.com",
        address="Tower B, Prestige Towers",
        city="Chennai",
        state="Tamil Nadu",
        pincode="600001",
        pan_number="IYERM5678B",
        aadhar_last_four="2222",
        kyc_verified=True,
        kyc_verification_date="2024-10-15",
        employer="Google",
        monthly_income=250000.0,
        account_status="ACTIVE"
    ),
    "9876543217": CRMCustomerRecord(
        customer_id="CUST008",
        full_name="Zainab Khan",
        phone="9876543217",
        email="zainab.khan@email.com",
        address="22, Old City",
        city="Lucknow",
        state="Uttar Pradesh",
        pincode="226001",
        pan_number="KHANZ9012C",
        aadhar_last_four="3333",
        kyc_verified=True,
        kyc_verification_date="2024-04-20",
        employer="Freelance",
        monthly_income=40000.0,
        account_status="ACTIVE"
    ),
    "9876543218": CRMCustomerRecord(
        customer_id="CUST009",
        full_name="Chris D'Souza",
        phone="9876543218",
        email="chris.dsouza@email.com",
        address="45, Bandra West",
        city="Mumbai",
        state="Maharashtra",
        pincode="400050",
        pan_number="DSOUC3456D",
        aadhar_last_four="4444",
        kyc_verified=True,
        kyc_verification_date="2024-07-25",
        employer="StartUp Inc",
        monthly_income=70000.0,
        account_status="ACTIVE"
    ),
    "9876543219": CRMCustomerRecord(
        customer_id="CUST010",
        full_name="Pooja Hegde",
        phone="9876543219",
        email="pooja.hegde@email.com",
        address="88, Koramangala",
        city="Bangalore",
        state="Karnataka",
        pincode="560034",
        pan_number="HEGDP7890E",
        aadhar_last_four="5555",
        kyc_verified=True,
        kyc_verification_date="2024-08-10",
        employer="HDFC Bank",
        monthly_income=90000.0,
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
    # NEW CREDIT RECORDS (6-10)
    "DASAJ1234A": CreditBureauRecord(  # Arjun Das
        pan_number="DASAJ1234A",
        credit_score=710,
        active_loans=1,
        total_outstanding=50000.0,
        payment_history_score=75,
        credit_utilization=45.0,
        oldest_account_age_months=24,
        recent_inquiries=4,
        delinquent_accounts=0
    ),
    "IYERM5678B": CreditBureauRecord(  # Meera Iyer - EXCELLENT
        pan_number="IYERM5678B",
        credit_score=850,
        active_loans=0,
        total_outstanding=0.0,
        payment_history_score=100,
        credit_utilization=10.0,
        oldest_account_age_months=144,
        recent_inquiries=0,
        delinquent_accounts=0
    ),
    "KHANZ9012C": CreditBureauRecord(  # Zainab Khan - BELOW THRESHOLD
        pan_number="KHANZ9012C",
        credit_score=690,  # Below 700
        active_loans=3,
        total_outstanding=200000.0,
        payment_history_score=60,
        credit_utilization=70.0,
        oldest_account_age_months=30,
        recent_inquiries=6,
        delinquent_accounts=1
    ),
    "DSOUC3456D": CreditBureauRecord(  # Chris D'Souza
        pan_number="DSOUC3456D",
        credit_score=740,
        active_loans=1,
        total_outstanding=150000.0,
        payment_history_score=85,
        credit_utilization=35.0,
        oldest_account_age_months=42,
        recent_inquiries=2,
        delinquent_accounts=0
    ),
    "HEGDP7890E": CreditBureauRecord(  # Pooja Hegde
        pan_number="HEGDP7890E",
        credit_score=790,
        active_loans=1,
        total_outstanding=80000.0,
        payment_history_score=94,
        credit_utilization=18.0,
        oldest_account_age_months=60,
        recent_inquiries=1,
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
    # NEW OFFERS (6-10)
    "CUST006": PreApprovedOffer(
        customer_id="CUST006",
        preapproved_limit=200000.0,
        interest_rate=14.5,
        max_tenure_months=36,
        offer_valid_until="2025-02-28",
        offer_type="BASIC"
    ),
    "CUST007": PreApprovedOffer(
        customer_id="CUST007",
        preapproved_limit=1000000.0,
        interest_rate=10.5,
        max_tenure_months=60,
        offer_valid_until="2025-06-30",
        offer_type="PLATINUM"
    ),
    "CUST008": PreApprovedOffer(  # Low credit - no offer
        customer_id="CUST008",
        preapproved_limit=0.0,
        interest_rate=18.0,
        max_tenure_months=24,
        offer_valid_until="2025-01-31",
        offer_type="NONE"
    ),
    "CUST009": PreApprovedOffer(
        customer_id="CUST009",
        preapproved_limit=450000.0,
        interest_rate=13.0,
        max_tenure_months=48,
        offer_valid_until="2025-04-30",
        offer_type="STANDARD"
    ),
    "CUST010": PreApprovedOffer(
        customer_id="CUST010",
        preapproved_limit=600000.0,
        interest_rate=12.0,
        max_tenure_months=60,
        offer_valid_until="2025-05-31",
        offer_type="PREMIUM"
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
