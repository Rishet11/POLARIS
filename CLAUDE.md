# CLAUDE.md — POLARIS

Project-specific instructions for Claude Code sessions in this repo. Global instructions still apply; this file adds context specific to POLARIS.

## What this repo is

POLARIS is an FSM-governed multi-agent system for financial back-office workflows. Two workflows run on one shared engine pattern (explicit state machines, hard guards, no improvisation):

1. **Loan Origination** — consumer personal-loan sales chatbot for an NBFC (non-bank lender). `master_agent.py`, `agents/`, `state.py`.
2. **Factoring Back Office** — payment reconciliation (cash application) and collections on factored invoices. `factoring/`.

## Architecture map

- `state.py` — origination FSM: states, allowed transitions, anti-loop guards (`MAX_AGENT_CALLS`, terminal states).
- `master_agent.py` — origination orchestrator; routes each turn to the right specialist agent based on FSM state.
- `agents/` — origination specialist agents (sales, underwriting, verification, sanction). `underwriting_agent.py` is rule-based.
- `config.py` — Gemini API setup, `DEMO_MODE` flag, model config.
- `factoring/models.py` — data models: `Debtor`, `Invoice`, `BankPayment`, status/tier/aging enums.
- `factoring/reconciliation_agent.py` — cash-application matching engine, rule-based, no LLM.
- `factoring/collections_fsm.py` — collections state machine: stages, guards, transitions.
- `factoring/collections_agent.py` — collections orchestrator; prioritizes cases, drives them through the FSM, drafts outreach text.
- `factoring/portfolio.py` — pure-function portfolio/covenant metrics computed from the same invoice/debtor models.
- `app.py` — Streamlit UI for both workflows.
- `tests/` — offline pytest suite; `tests/conftest.py` mocks the Gemini API so nothing hits the network.

## Test commands

```bash
pytest -q
```

All tests are offline: the LLM is mocked in `tests/conftest.py`, so no API key or network access is needed to run the suite. Run this before any commit.

## Durable engineering rules — do not weaken

- **Reconciliation stays rule-based.** `factoring/reconciliation_agent.py` has no LLM in the matching path. Confidence tiers (100 exact ref+amount / 90 unambiguous amount / 70-89 probable match, human review / <70 exception queue) are deterministic. A wrong auto-match moves real money — never make matching LLM-driven or probabilistic without a human-in-the-loop gate.
- **The review queue is actionable.** Auto-applied tiers and human approve/reject decisions both mutate ledger state through the same `apply_match` / `reject_match` path (`factoring/reconciliation_agent.py`), so system and human actions can never diverge in how they update an invoice. Every decision, from either path, produces a structured, timestamped audit entry.
- **FSM guards must never be weakened.** Both `state.py` (origination) and `factoring/collections_fsm.py` (collections) use explicit transition tables and hard guards: a debtor/customer cannot be messaged twice with identical content, escalation requires meeting a minimum threshold of unanswered attempts, and every case has an action cap and terminal states that block further transitions. Additions should only add guards or tests, never loosen an existing one.
- **`DEMO_MODE` contract.** `config.py` auto-enables `DEMO_MODE` when no `GOOGLE_API_KEY` is set. Any agent that calls Gemini must check this flag and fall back to a canned/template response, so a hosted demo never errors on camera for lack of a key.
- **New logic needs offline tests.** Follow the existing style (see `tests/test_reconciliation.py`, `tests/test_collections_fsm.py`): fixture-driven, deterministic, no network calls, one behavior asserted per test.

## What NOT to do here

- Don't touch `landing_page/index.html` copy without also checking `README.md` for consistency — they describe the same mechanisms and should not drift apart.
- Don't commit `graphify-out/`, `.agents/`, or `__pycache__/` — all gitignored on purpose.
- Don't deploy or send any outreach without the user's explicit go-ahead.
