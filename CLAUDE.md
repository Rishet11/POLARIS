# CLAUDE.md — POLARIS

Project-specific instructions for Claude Code sessions in this repo. Global instructions in `~/.claude/CLAUDE.md` still apply; this file adds context specific to POLARIS.

## What this repo is

A hackathon project repurposed as an internship demo for **Isabela Rodriguez, CEO of Zolvo** (YC S26, AI back-office automation for commercial factoring/ABL lenders). See [context.md](context.md) for the full backstory, why this pivot happened, and the domain vocabulary being targeted.

Two workflows on one FSM engine:
1. **Loan Origination** (original hackathon build) — consumer personal-loan sales chatbot, India NBFC. `master_agent.py`, `agents/`, `state.py`.
2. **Factoring Back Office** (built for the Zolvo pitch) — cash-application (payment reconciliation) and collections on factored invoices. `factoring/`.

## Ground truth, not the plan file

`/Users/rishetmehra/.claude/plans/u-remmeber-i-was-starry-walrus.md` has the original plan. Treat it as historical intent, not current state — check the code before assuming a phase is done. As of this writing: factoring package, tests, README, and DEMO_MODE fallback are built and committed to the working tree (uncommitted to git — see `git status`). Hosting, the Loom recording, and the reply email are NOT done.

## Non-negotiable framing rule

The original cold email to Isabela claimed POLARIS handles "underwriting and collections." **Underwriting was real; collections was not** — this repo's `factoring/` package exists specifically to make that claim true after the fact. Never reintroduce language that implies collections was already built before this work, and never describe this as "adapting" the demo for Zolvo — Isabela did collections AI at Domu (YC S24) and will read "adapted" as backfilling an overclaim. Frame it as: built after studying Zolvo's product, using their own vocabulary (cash application, account debtor, aging bucket, exception queue, dilution, confidence tiers).

## Domain rules baked into the code — do not weaken

- `factoring/reconciliation_agent.py`: rule-based, **no LLM**. Confidence tiers (100/90/70-89/<70) mirror Zolvo's own public framing. A wrong auto-match moves real money — never make this LLM-driven or probabilistic without a human-in-the-loop gate.
- `factoring/collections_fsm.py` / `collections_agent.py`: same anti-loop pattern as `state.py` — a debtor cannot be dunned twice with the same message, escalation requires ≥2 unanswered outreaches. This is the "agents can't improvise" story; don't relax the guards to make a demo flow smoother.
- `config.py` `DEMO_MODE`: auto-enables when no `GOOGLE_API_KEY` is set. Any new agent that calls Gemini must respect this flag with a canned/template fallback, or a hosted demo will error on camera.

## Testing

`pytest` — 71 tests, all offline (LLM mocked via `tests/conftest.py`). Run this before any commit. New agents/rules need tests in the same style (see `tests/test_reconciliation.py`, `tests/test_collections_fsm.py` for the factoring-side pattern).

## Knowledge graph

`graphify-out/` holds a rebuilt knowledge graph (479 nodes, 886 edges, 23 communities) covering both workflows. It's gitignored (regenerable cache) — re-run `/graphify .` after significant structural changes, not after every commit. See `graphify-out/GRAPH_REPORT.md` for God Nodes, surprising connections, and open verification questions (several INFERRED edges around `MasterAgent` and `CollectionsAgent` are unverified — worth a `graphify explain` pass if touching that code).

## What NOT to do here

- Don't touch `landing_page/index.html` copy without also checking `README.md` — graphify flagged them as `semantically_similar_to` at 0.85-0.95 confidence, meaning they currently describe the same mechanisms almost 1:1. Letting them drift creates the exact kind of inconsistency this whole exercise is trying to avoid.
- Don't commit `graphify-out/`, `.agents/`, or `__pycache__/` — all gitignored on purpose.
- Don't deploy or send the outreach email without the user's explicit go-ahead (see global CLAUDE.md: no pushing/sending without asking).
