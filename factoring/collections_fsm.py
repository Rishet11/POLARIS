"""
POLARIS Collections FSM
Finite-state machine for collecting on a past-due factored invoice.
Same governance philosophy as the origination FSM in state.py:
explicit transitions, hard guards, and anti-loop safeguards — the
agent structurally cannot re-send a message or skip an escalation gate.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class CollectionStage(str, Enum):
    PRIORITIZE = "PRIORITIZE"          # case created, priority scored
    OUTREACH = "OUTREACH"              # drafting/sending a reminder
    AWAIT_RESPONSE = "AWAIT_RESPONSE"  # reminder sent, waiting on debtor
    PROMISE_TO_PAY = "PROMISE_TO_PAY"  # debtor committed to a date
    DISPUTE_INTAKE = "DISPUTE_INTAKE"  # debtor disputes — human queue, dilution reserve
    ESCALATE = "ESCALATE"              # human escalation (gated: ≥2 unanswered outreaches)
    RESOLVED = "RESOLVED"              # terminal: paid / settled
    WRITTEN_OFF = "WRITTEN_OFF"        # terminal: uncollectable


# Explicit transition table — anything not listed here is illegal.
ALLOWED_TRANSITIONS: Dict[CollectionStage, Set[CollectionStage]] = {
    CollectionStage.PRIORITIZE: {CollectionStage.OUTREACH},
    CollectionStage.OUTREACH: {CollectionStage.AWAIT_RESPONSE},
    CollectionStage.AWAIT_RESPONSE: {
        CollectionStage.OUTREACH,
        CollectionStage.PROMISE_TO_PAY,
        CollectionStage.DISPUTE_INTAKE,
        CollectionStage.ESCALATE,
    },
    CollectionStage.PROMISE_TO_PAY: {
        CollectionStage.RESOLVED,
        CollectionStage.OUTREACH,  # broken promise → back to outreach
    },
    CollectionStage.DISPUTE_INTAKE: {
        CollectionStage.RESOLVED,
        CollectionStage.WRITTEN_OFF,
    },
    CollectionStage.ESCALATE: {
        CollectionStage.RESOLVED,
        CollectionStage.WRITTEN_OFF,
    },
    CollectionStage.RESOLVED: set(),
    CollectionStage.WRITTEN_OFF: set(),
}

TERMINAL_STAGES = {CollectionStage.RESOLVED, CollectionStage.WRITTEN_OFF}

# Escalation gate: a case may only escalate after this many unanswered outreaches
MIN_OUTREACHES_BEFORE_ESCALATION = 2

# Hard cap on FSM actions per case (mirrors MAX_AGENT_CALLS in origination)
MAX_ACTIONS_PER_CASE = 10

# Dunning ladder: 1st touch WhatsApp, 2nd email, 3rd+ escalates to a phone
# call task. Chosen deterministically from outreach_count — never a model
# decision, so the channel a debtor sees on attempt N is always the same.
DUNNING_CHANNEL_LADDER = ["whatsapp", "email", "phone"]


class CollectionOutcome(str, Enum):
    """Result of attempting an FSM action."""
    OK = "OK"
    BLOCKED_ILLEGAL_TRANSITION = "BLOCKED_ILLEGAL_TRANSITION"
    BLOCKED_DUPLICATE_MESSAGE = "BLOCKED_DUPLICATE_MESSAGE"
    BLOCKED_ESCALATION_GATE = "BLOCKED_ESCALATION_GATE"
    BLOCKED_MAX_ACTIONS = "BLOCKED_MAX_ACTIONS"
    BLOCKED_TERMINAL = "BLOCKED_TERMINAL"


@dataclass
class CollectionCase:
    """One past-due invoice being collected."""
    case_id: str
    invoice_id: str
    debtor_id: str
    open_amount: float
    factored_amount: float
    aging_bucket: str
    priority_score: float
    stage: CollectionStage = CollectionStage.PRIORITIZE

    outreach_count: int = 0
    sent_message_hashes: List[str] = field(default_factory=list)
    channel_history: List[str] = field(default_factory=list)
    total_actions: int = 0
    history: List[str] = field(default_factory=list)

    promise_date: Optional[date] = None
    dispute_reason: Optional[str] = None
    dilution_reserve: float = 0.0

    # ------------------------------------------------------------------
    # Guards
    # ------------------------------------------------------------------

    def is_terminal(self) -> bool:
        return self.stage in TERMINAL_STAGES

    def _guard(self, target: CollectionStage) -> Optional[CollectionOutcome]:
        """Common guards for every transition. Returns a block reason or None."""
        if self.is_terminal():
            return CollectionOutcome.BLOCKED_TERMINAL
        if self.total_actions >= MAX_ACTIONS_PER_CASE:
            return CollectionOutcome.BLOCKED_MAX_ACTIONS
        if target not in ALLOWED_TRANSITIONS[self.stage]:
            return CollectionOutcome.BLOCKED_ILLEGAL_TRANSITION
        return None

    def _move(self, target: CollectionStage, note: str) -> CollectionOutcome:
        blocked = self._guard(target)
        if blocked:
            self.history.append(f"BLOCKED {self.stage.value}→{target.value}: {blocked.value}")
            return blocked
        self.history.append(f"{self.stage.value}→{target.value}: {note}")
        self.stage = target
        self.total_actions += 1
        return CollectionOutcome.OK

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def start_outreach(self) -> CollectionOutcome:
        return self._move(CollectionStage.OUTREACH, "outreach cycle started")

    def current_channel(self) -> str:
        """
        Next channel in the dunning ladder, chosen deterministically from
        outreach_count: 1st touch WhatsApp, 2nd email, 3rd+ phone escalation.
        """
        index = min(self.outreach_count, len(DUNNING_CHANNEL_LADDER) - 1)
        return DUNNING_CHANNEL_LADDER[index]

    def send_message(
        self, message: str, channel: Optional[str] = None
    ) -> Tuple[CollectionOutcome, Optional[str]]:
        """
        Send a dunning message on a channel (defaults to the next rung of
        the dunning ladder). Anti-loop guard: the same message content can
        never be sent twice on a case.
        Returns (outcome, message_or_None).
        """
        channel = channel or self.current_channel()
        msg_hash = hashlib.md5(message.strip().lower().encode()).hexdigest()[:12]
        if msg_hash in self.sent_message_hashes:
            self.history.append(
                f"BLOCKED send in {self.stage.value}: duplicate message (hash {msg_hash})"
            )
            return CollectionOutcome.BLOCKED_DUPLICATE_MESSAGE, None

        outcome = self._move(CollectionStage.AWAIT_RESPONSE,
                             f"reminder #{self.outreach_count + 1} sent via {channel}")
        if outcome is not CollectionOutcome.OK:
            return outcome, None

        self.sent_message_hashes.append(msg_hash)
        self.channel_history.append(channel)
        self.outreach_count += 1
        return CollectionOutcome.OK, message

    def record_promise(self, promise_date: date) -> CollectionOutcome:
        outcome = self._move(CollectionStage.PROMISE_TO_PAY,
                             f"debtor promised payment by {promise_date.isoformat()}")
        if outcome is CollectionOutcome.OK:
            self.promise_date = promise_date
        return outcome

    def record_dispute(self, reason: str) -> CollectionOutcome:
        outcome = self._move(CollectionStage.DISPUTE_INTAKE, f"dispute raised: {reason}")
        if outcome is CollectionOutcome.OK:
            self.dispute_reason = reason
            # Reserve the full open amount as potential dilution until resolved
            self.dilution_reserve = self.open_amount
        return outcome

    def escalate(self) -> CollectionOutcome:
        """Escalate to a human. Gated: requires ≥2 unanswered outreaches."""
        if (self.stage == CollectionStage.AWAIT_RESPONSE
                and self.outreach_count < MIN_OUTREACHES_BEFORE_ESCALATION):
            self.history.append(
                f"BLOCKED {self.stage.value}→ESCALATE: escalation gate "
                f"({self.outreach_count}/{MIN_OUTREACHES_BEFORE_ESCALATION} outreaches)"
            )
            return CollectionOutcome.BLOCKED_ESCALATION_GATE
        return self._move(CollectionStage.ESCALATE, "escalated to human collector")

    def resolve(self, note: str = "payment received") -> CollectionOutcome:
        outcome = self._move(CollectionStage.RESOLVED, note)
        if outcome is CollectionOutcome.OK:
            self.dilution_reserve = 0.0
        return outcome

    def write_off(self, note: str = "deemed uncollectable") -> CollectionOutcome:
        return self._move(CollectionStage.WRITTEN_OFF, note)

    def broken_promise(self) -> CollectionOutcome:
        return self._move(CollectionStage.OUTREACH, "promise date passed unpaid")

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "invoice_id": self.invoice_id,
            "debtor_id": self.debtor_id,
            "open_amount": self.open_amount,
            "aging_bucket": self.aging_bucket,
            "priority_score": round(self.priority_score, 0),
            "stage": self.stage.value,
            "outreach_count": self.outreach_count,
            "total_actions": self.total_actions,
            "dilution_reserve": self.dilution_reserve,
            "channel_history": list(self.channel_history),
            "next_channel": self.current_channel(),
        }
