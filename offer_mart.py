"""
POLARIS Offer Mart
Mock customer database with preapproved offers.
Designed for easy replacement with real APIs.
"""

from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class CustomerProfile:
    """Customer profile from Offer Mart."""
    customer_id: str
    name: str
    phone: str
    email: str
    credit_score: int
    preapproved_limit: float
    interest_rate: float
    max_tenure_months: int
    employer: Optional[str] = None
    monthly_salary: Optional[float] = None
    kyc_verified: bool = False


# Mock customer database
CUSTOMER_DATABASE: Dict[str, CustomerProfile] = {
    # Good credit customers
    "9876543210": CustomerProfile(
        customer_id="CUST001",
        name="Rahul Sharma",
        phone="9876543210",
        email="rahul.sharma@email.com",
        credit_score=780,
        preapproved_limit=500000.0,
        interest_rate=12.5,
        max_tenure_months=60,
        employer="TCS",
        monthly_salary=85000.0,
        kyc_verified=True,
    ),
    "9876543211": CustomerProfile(
        customer_id="CUST002",
        name="Priya Patel",
        phone="9876543211",
        email="priya.patel@email.com",
        credit_score=820,
        preapproved_limit=750000.0,
        interest_rate=11.0,
        max_tenure_months=72,
        employer="Infosys",
        monthly_salary=120000.0,
        kyc_verified=True,
    ),
    "9876543212": CustomerProfile(
        customer_id="CUST003",
        name="Amit Kumar",
        phone="9876543212",
        email="amit.kumar@email.com",
        credit_score=750,
        preapproved_limit=300000.0,
        interest_rate=13.5,
        max_tenure_months=48,
        employer="Wipro",
        monthly_salary=65000.0,
        kyc_verified=True,
    ),
    
    # Low credit score customer (for rejection testing)
    "9876543213": CustomerProfile(
        customer_id="CUST004",
        name="Vikram Singh",
        phone="9876543213",
        email="vikram.singh@email.com",
        credit_score=650,  # Below 700 threshold
        preapproved_limit=0.0,
        interest_rate=18.0,
        max_tenure_months=24,
        employer="Self-employed",
        monthly_salary=45000.0,
        kyc_verified=True,
    ),
    
    # Unverified KYC customer
    "9876543214": CustomerProfile(
        customer_id="CUST005",
        name="Sneha Reddy",
        phone="9876543214",
        email="sneha.reddy@email.com",
        credit_score=760,
        preapproved_limit=400000.0,
        interest_rate=12.0,
        max_tenure_months=48,
        employer="Amazon",
        monthly_salary=95000.0,
        kyc_verified=False,  # KYC not verified
    ),
}


def lookup_customer_by_phone(phone: str) -> Optional[CustomerProfile]:
    """
    Look up customer by phone number.
    Returns None if customer not found.
    """
    # Normalize phone number
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+91"):
        phone = phone[3:]
    if phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]
    
    return CUSTOMER_DATABASE.get(phone)


def lookup_customer_by_id(customer_id: str) -> Optional[CustomerProfile]:
    """
    Look up customer by customer ID.
    Returns None if customer not found.
    """
    for profile in CUSTOMER_DATABASE.values():
        if profile.customer_id == customer_id:
            return profile
    return None


def get_preapproved_offer(phone: str) -> Optional[Dict]:
    """
    Get preapproved offer for a customer.
    Returns formatted offer details.
    """
    customer = lookup_customer_by_phone(phone)
    if not customer:
        return None
    
    if customer.credit_score < 700:
        return None
    
    return {
        "customer_id": customer.customer_id,
        "customer_name": customer.name,
        "preapproved_limit": customer.preapproved_limit,
        "interest_rate": customer.interest_rate,
        "max_tenure_months": customer.max_tenure_months,
        "credit_score": customer.credit_score,
    }


def calculate_emi(principal: float, rate: float, tenure_months: int) -> float:
    """
    Calculate EMI using standard formula.
    rate is annual percentage, tenure in months.
    """
    monthly_rate = rate / 12 / 100
    if monthly_rate == 0:
        return principal / tenure_months
    
    emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure_months) / (((1 + monthly_rate) ** tenure_months) - 1)
    return round(emi, 2)
