"""
POLARIS Conversation State Management
Implements the finite-state machine for loan conversations.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal, List
from enum import Enum


class Stage(str, Enum):
    """Conversation stages (finite states)."""
    INTRO = "INTRO"
    NEED_DISCOVERY = "NEED_DISCOVERY"
    OFFER_PRESENTATION = "OFFER_PRESENTATION"
    KYC_VERIFICATION = "KYC_VERIFICATION"
    UNDERWRITING = "UNDERWRITING"
    DOCUMENT_COLLECTION = "DOCUMENT_COLLECTION"
    SANCTION = "SANCTION"
    REJECTION = "REJECTION"
    END = "END"


class Decision(str, Enum):
    """Underwriting decisions."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"
    NEED_SALARY_SLIP = "NEED_SALARY_SLIP"


class TerminalState(str, Enum):
    """Terminal states for conversation end."""
    LOAN_SANCTIONED = "LOAN_SANCTIONED"
    LOAN_REJECTED = "LOAN_REJECTED"
    ADDITIONAL_DOCUMENT_REQUIRED = "ADDITIONAL_DOCUMENT_REQUIRED"
    CUSTOMER_DROPPED = "CUSTOMER_DROPPED"


@dataclass
class ConversationState:
    """
    Central state object for the conversation.
    Updated at every step by the Master Agent.
    """
    # Current stage in the state machine
    stage: Stage = Stage.INTRO
    
    # Customer identification
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    pan_number: Optional[str] = None
    
    # Loan request details
    requested_amount: Optional[float] = None
    tenure_months: Optional[int] = None
    purpose: Optional[str] = None
    
    # Credit profile (from Offer Mart)
    preapproved_limit: Optional[float] = None
    credit_score: Optional[int] = None
    
    # Income details
    salary: Optional[float] = None
    employer: Optional[str] = None
    
    # Calculated values
    emi: Optional[float] = None
    interest_rate: Optional[float] = None
    
    # Verification status
    kyc_verified: bool = False
    salary_slip_received: bool = False
    
    # Decision tracking
    decision: Optional[Decision] = None
    rejection_reason: Optional[str] = None
    
    # Sanction details
    sanction_id: Optional[str] = None
    
    # Terminal state
    terminal_state: Optional[TerminalState] = None
    
    # Anti-loop tracking
    last_agent_called: Optional[str] = None
    agent_call_history: List[str] = field(default_factory=list)
    total_agent_calls: int = 0
    
    # Conversation history
    messages: List[dict] = field(default_factory=list)
    
    def is_terminal(self) -> bool:
        """Check if conversation has reached a terminal state."""
        return self.terminal_state is not None
    
    def can_call_agent(self, agent_name: str, input_hash: str) -> bool:
        """
        Check if an agent can be called (anti-loop safeguard).
        Returns False if same agent was called with same inputs.
        """
        call_signature = f"{agent_name}:{input_hash}"
        if call_signature in self.agent_call_history:
            return False
        return True
    
    def record_agent_call(self, agent_name: str, input_hash: str):
        """Record an agent call for anti-loop tracking."""
        call_signature = f"{agent_name}:{input_hash}"
        self.agent_call_history.append(call_signature)
        self.last_agent_called = agent_name
        self.total_agent_calls += 1
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.messages.append({"role": role, "content": content})
    
    def to_dict(self) -> dict:
        """Convert state to dictionary for display."""
        return {
            "stage": self.stage.value if self.stage else None,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "requested_amount": self.requested_amount,
            "tenure_months": self.tenure_months,
            "preapproved_limit": self.preapproved_limit,
            "credit_score": self.credit_score,
            "salary": self.salary,
            "emi": self.emi,
            "kyc_verified": self.kyc_verified,
            "salary_slip_received": self.salary_slip_received,
            "decision": self.decision.value if self.decision else None,
            "terminal_state": self.terminal_state.value if self.terminal_state else None,
            "total_agent_calls": self.total_agent_calls,
        }
