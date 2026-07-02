## 2026-07-02T18:22:18Z
You are a Safeguard Test Developer (Worker) for the POLARIS test suite.
Your working directory is /Users/rishetmehra/Desktop/Findinternships/POLARIS-clone/.agents/worker_safeguards/.
Please create all coordinates under /Users/rishetmehra/Desktop/Findinternships/POLARIS-clone/.agents/worker_safeguards/.

## Objective
Write a comprehensive test file `tests/test_safeguards.py` that validates all system safeguards: the anti-loop checks (for VerificationAgent and UnderwritingAgent), the maximum agent calls limit safeguard, and the actual PDF generation behavior of SanctionAgent.

## Requirements
Ensure there are test cases verifying:
1. Anti-Loop Safeguard:
   - Call `ConversationState.can_call_agent()` and `record_agent_call()` to verify basic signature tracking.
   - Simulate a flow where `VERIFICATION_AGENT` is called twice with the identical phone number input, checking that `MasterAgent` returns: `"There was an issue with the verification process. Please try again later."` and sets the stage to `Stage.END` and terminal state to `TerminalState.LOAN_REJECTED`.
   - Simulate a flow where `UNDERWRITING_AGENT` is called twice with the identical inputs, checking that `MasterAgent` returns: `"We encountered an issue processing your application. Please try again later."` and sets the stage to `Stage.END` and terminal state to `TerminalState.CUSTOMER_DROPPED`.
2. Max Agent Calls Safeguard:
   - Instantiate a `MasterAgent` and set `self.state.total_agent_calls = 6`.
   - Call `process_message("Any message")` and verify that the safeguard triggers immediately, returning `"Maximum agent calls exceeded. Conversation ended."` and sets `self.state.stage = Stage.END` and `self.state.terminal_state = TerminalState.CUSTOMER_DROPPED`.
3. PDF Generation Verification:
   - Write a test that runs `SanctionAgent` with mock inputs, checking that the output PDF is successfully created on the file system (if `FPDF_AVAILABLE` is True), is non-empty, and cleans up the PDF file afterward.

## Scope Boundaries
- Do NOT modify any core files of the POLARIS application (e.g. app.py, master_agent.py, agents/*.py, config.py, mock_apis.py, offer_mart.py, state.py). Only add/edit files in the `tests/` directory.
- DO NOT hardcode test results.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please execute these tests, run pytest to ensure they pass, and write your completion handoff report to `/Users/rishetmehra/Desktop/Findinternships/POLARIS-clone/.agents/worker_safeguards/handoff.md`. Include the details of the created test file and the test execution output.
