"""
POLARIS Factoring Data Models
Debtors, factored invoices, and incoming bank payments.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import List, Optional


class InvoiceStatus(str, Enum):
    OUTSTANDING = "OUTSTANDING"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    DISPUTED = "DISPUTED"
    SHORT_PAY = "SHORT_PAY"


class MatchTier(str, Enum):
    """Confidence tiers for cash application."""
    AUTO_APPLY = "AUTO_APPLY"                # exact reference + amount, no review
    AUTO_APPLY_LOGGED = "AUTO_APPLY_LOGGED"  # unambiguous, applied with audit log
    REVIEW = "REVIEW"                        # flagged for one-click human review
    EXCEPTION = "EXCEPTION"                  # routed to exception queue


class AgingBucket(str, Enum):
    CURRENT = "CURRENT"
    DAYS_1_30 = "1-30"
    DAYS_31_60 = "31-60"
    DAYS_61_90 = "61-90"
    DAYS_90_PLUS = "90+"


@dataclass
class Debtor:
    """Account debtor (the party that owes on the factored invoice)."""
    debtor_id: str
    name: str
    contact_email: str
    payment_terms_days: int = 30
    dispute_history_count: int = 0


@dataclass
class Invoice:
    """A factored invoice purchased from the client."""
    invoice_id: str
    debtor_id: str
    face_amount: float
    invoice_date: date
    due_date: date
    reference_no: str
    advance_rate: float = 0.85
    status: InvoiceStatus = InvoiceStatus.OUTSTANDING
    paid_amount: float = 0.0

    @property
    def factored_amount(self) -> float:
        """Amount advanced to the client against this invoice."""
        return round(self.face_amount * self.advance_rate, 2)

    @property
    def open_amount(self) -> float:
        """Unpaid balance on the invoice face."""
        return round(self.face_amount - self.paid_amount, 2)

    @property
    def is_open(self) -> bool:
        return self.status in (
            InvoiceStatus.OUTSTANDING,
            InvoiceStatus.PARTIAL,
            InvoiceStatus.SHORT_PAY,
        )

    def days_past_due(self, as_of: Optional[date] = None) -> int:
        as_of = as_of or date.today()
        return max(0, (as_of - self.due_date).days)

    def aging_bucket(self, as_of: Optional[date] = None) -> AgingBucket:
        dpd = self.days_past_due(as_of)
        if dpd == 0:
            return AgingBucket.CURRENT
        if dpd <= 30:
            return AgingBucket.DAYS_1_30
        if dpd <= 60:
            return AgingBucket.DAYS_31_60
        if dpd <= 90:
            return AgingBucket.DAYS_61_90
        return AgingBucket.DAYS_90_PLUS


@dataclass
class BankPayment:
    """An incoming payment on the bank feed, pre-reconciliation."""
    payment_id: str
    value_date: date
    amount: float
    payer_name: str
    reference_text: str  # free text from the wire/ACH memo, often messy
    matched_invoice_ids: List[str] = field(default_factory=list)
    match_confidence: Optional[int] = None
    match_tier: Optional[MatchTier] = None
    match_reason: Optional[str] = None
    applied: bool = False


def days_ago(n: int) -> date:
    return date.today() - timedelta(days=n)


def days_ahead(n: int) -> date:
    return date.today() + timedelta(days=n)
