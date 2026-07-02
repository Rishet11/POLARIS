# Original User Request

## Initial Request — 2026-07-02T18:14:42Z

Develop a comprehensive, automated test suite that tests every feature and state transition of the POLARIS multi-agent system.

Working directory: /Users/rishetmehra/Desktop/Findinternships/POLARIS-clone
Integrity mode: development

## Requirements

### R1. State Machine & Flow Verification
Develop programmatic tests that verify all 9 FSM state transitions and 4 terminal outcomes governed by the `MasterAgent` and `ConversationState`.

### R2. Agent Logic Verification
Verify the distinct logic for all 4 sub-agents: `SalesAgent` (data extraction), `VerificationAgent` (mock CRM lookup), `UnderwritingAgent` (deterministic rules), and `SanctionAgent` (PDF generation).

### R3. API Mocking
Since the live Gemini LLM API is currently failing due to quota limits, you must mock out the LLM calls (e.g., using `unittest.mock`) so that the test suite can execute and pass completely offline without needing a funded API key.

## Acceptance Criteria

### Execution
- [ ] The test suite can be executed locally via a standard test runner (e.g., `pytest`) or a single Python entry script.
- [ ] The test suite executes and passes without any external LLM API quota required.

### Coverage
- [ ] At least one automated test verifies the `UnderwritingAgent` deterministic rules (e.g., rejecting credit < 700).
- [ ] At least one automated test verifies the anti-loop safeguard in `ConversationState`.
- [ ] At least one automated test verifies that the `SanctionAgent` successfully generates a PDF file.
