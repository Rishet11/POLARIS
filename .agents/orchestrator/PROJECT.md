# Project: POLARIS Test Suite Development

## Architecture
POLARIS is a multi-agent loan conversation flow system built around a finite-state machine (FSM). The FSM is managed by `MasterAgent` using `ConversationState`. The sub-agents (`SalesAgent`, `VerificationAgent`, `UnderwritingAgent`, `SanctionAgent`) handle specific processing tasks.

The test suite will verify the system offline, simulating LLM API responses and CRM/Credit Bureau API mock data.

### Test Components:
- **Mock LLM Layer**: Utility mock (patching `google.generativeai` and `config.get_model`) to return structured JSON responses for various agent inputs.
- **FSM Tests (`test_fsm.py`)**: Checks all 9 state transitions and 4 terminal outcomes of `MasterAgent`.
- **Agent Logic Tests (`test_agents.py`)**: Checks distinct processing logic for each of the 4 sub-agents.
- **Safeguards & Coverage Tests (`test_safeguards.py`)**: Tests the anti-loop tracking, agent call limit, and PDF generation by `SanctionAgent`.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Setup & Mocking Design | Establish test framework (pytest), design Gemini/LLM mocking utilities. | None | DONE |
| 2 | FSM & Transition Tests | Verify all 9 FSM transitions and 4 terminal outcomes under MasterAgent. | M1 | DONE |
| 3 | Agent Logic Tests | Verify distinct input processing and logic in the 4 sub-agents. | M1 | DONE |
| 4 | Safeguards & Coverage | Verify underwriting rules, anti-loop safeguard, and PDF generation. | M1, M2, M3 | DONE |
| 5 | Integration & Sign-off | Run all tests, ensure zero-dependency on live API keys, check coverage. | M4 | DONE |

## Interface Contracts
- **Test Entry Point**: Runs via `pytest` or `python -m pytest` at the project root.
- **Gemini Mocking**:
  - `config.get_model` must return a mock object where `generate_content` returns an object with a `text` attribute containing valid JSON string outputs for agent processors.
- **Verification**: Output must verify that all 9 transitions and 4 outcomes are executed and verified.
