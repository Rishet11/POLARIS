# POLARIS 🌟

**FSM-governed multi-agent system for high-stakes financial workflows**

AI agents are a liability in financial operations when they can loop, improvise, or act twice on the same input. POLARIS puts every agent inside a strict finite-state machine: transitions are whitelisted, duplicate actions are structurally blocked, and anything the system can't resolve with confidence goes to a human queue instead of a guess.

Two workflows run on the same engine:

1. **Loan Origination** — a conversational flow from need discovery through KYC, underwriting, and sanction.
2. **Factoring Back Office** — cash application (payment reconciliation) and collections for factored receivables.

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

That's it — with no API key the app runs in demo mode with canned LLM responses. For live Gemini-drafted messages:

```bash
cp .env.example .env   # add your GOOGLE_API_KEY
```

Run the test suite (70 tests, fully offline):

```bash
pytest
```

---

## 🏦 Factoring Back Office

### Cash application
Incoming bank payments are matched to open invoices by deterministic rules, never an LLM — a wrong automatic match moves real money to the wrong ledger. Every match gets a confidence tier:

| Confidence | Tier | What happens |
|---|---|---|
| 100 | AUTO_APPLY | Exact reference + amount. Applied, no review. |
| 90 | AUTO_APPLY_LOGGED | Unambiguous amount match. Applied with an audit-log entry. |
| 70–89 | REVIEW | Probable match (short-pay, combined remittance, partial payment). Suggested, waits for a human. |
| <70 | EXCEPTION | Ambiguous or no signal. Routed to the exception queue. |

The demo bank feed is deliberately messy: wire-fee short-pays, one wire covering three invoices, a reused PO reference matching two invoices, and unreferenced payments with colliding amounts.

### Collections
Past-due invoices are ranked by priority (factored amount × aging-bucket weight × dispute history) and each case runs inside its own FSM:

```
PRIORITIZE → OUTREACH → AWAIT_RESPONSE → {PROMISE_TO_PAY | DISPUTE_INTAKE | ESCALATE}
                                       → RESOLVED | WRITTEN_OFF
```

Hard guards, not prompt instructions:
- The same dunning message can never be sent twice (content-hash check).
- Escalation is gated behind two unanswered outreaches.
- Terminal cases reject all further actions.
- Every case caps at 10 FSM actions.
- Blocked attempts are recorded in the case history — you can watch the FSM refuse.

The LLM only drafts message wording. Who to contact, when, and what happens next is deterministic.

---

## 💬 Loan Origination

A Master Agent routes a customer conversation through nine states (INTRO → NEED_DISCOVERY → OFFER_PRESENTATION → KYC_VERIFICATION → UNDERWRITING → DOCUMENT_COLLECTION → SANCTION/REJECTION → END) with four worker agents:

| Agent | Role | Logic |
|---|---|---|
| Sales | Extract loan requirements | LLM (low temperature) |
| Verification | KYC check via CRM | Rules |
| Underwriting | Credit decision | Rules (score gate, limit tiers, EMI affordability) |
| Sanction | Sanction letter PDF | Deterministic generation |

Anti-loop safeguards: max 6 agent calls per conversation, and the same agent can never be called twice with identical inputs.

Test customers are listed in the app sidebar (e.g. `9876543210` approves, `9876543213` rejects on credit score).

---

## 🏗️ Architecture

```
├── app.py                       # Streamlit UI (both workflows)
├── master_agent.py              # Origination FSM orchestrator
├── state.py                     # Origination state machine
├── config.py                    # Gemini config + demo mode
├── mock_apis.py                 # Mock CRM / credit bureau / offers
├── agents/                      # Origination worker agents
├── factoring/
│   ├── models.py                # Debtors, invoices, bank payments
│   ├── mock_data.py             # Deliberately messy demo bank feed
│   ├── reconciliation_agent.py  # Confidence-tiered cash application
│   ├── collections_fsm.py       # Collections state machine + guards
│   └── collections_agent.py     # Prioritization, outreach, response routing
└── tests/                       # 70 offline tests incl. headless UI walkthrough
```

All external integrations (CRM, credit bureau, bank feed) are mocked behind thin API classes designed to be swapped for real ones — the FSM and matching logic don't know the difference.

**Roadmap:** borrowing-base tracking, covenant/concentration monitoring, real bank-feed ingestion (MT940/Plaid).
