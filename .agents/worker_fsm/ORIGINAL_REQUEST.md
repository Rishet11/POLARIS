## 2026-07-02T18:18:40Z

You are an FSM Test Developer (Worker) for the POLARIS test suite.
Your working directory is /Users/rishetmehra/Desktop/Findinternships/POLARIS-clone/.agents/worker_fsm/.
Please create all coordinates under /Users/rishetmehra/Desktop/Findinternships/POLARIS-clone/.agents/worker_fsm/.

## Objective
Write a comprehensive test file `tests/test_fsm.py` that validates all 9 FSM transitions and 4 terminal outcomes of `MasterAgent` and `ConversationState`.

## FSM Transition Coverage Requirements
Ensure there are test cases verifying:
1. `INTRO` -> `NEED_DISCOVERY` (Initial greeting)
2. `NEED_DISCOVERY` -> `OFFER_PRESENTATION` (Pre-approved limit found, e.g. using Rahul Sharma "9876543210")
3. `NEED_DISCOVERY` -> `END` with `TerminalState.LOAN_REJECTED` (Low credit score, e.g. Vikram Singh "9876543213")
4. `NEED_DISCOVERY` -> `END` with `TerminalState.CUSTOMER_DROPPED` (Phone not found, e.g. "9999999999")
5. `OFFER_PRESENTATION` -> `END` with `TerminalState.CUSTOMER_DROPPED` (Customer declines offer, e.g. "No, not interested")
6. `OFFER_PRESENTATION` -> `KYC_VERIFICATION` (Transitioning to KYC during normal request)
7. `KYC_VERIFICATION` -> `UNDERWRITING` (KYC verified and moves to underwriting checks)
8. `KYC_VERIFICATION` -> `END` with `TerminalState.LOAN_REJECTED` (KYC verification fails, e.g. Sneha Reddy "9876543214")
9. `UNDERWRITING` -> `SANCTION` (Approved instantly when requested amount <= preapproved limit)
10. `UNDERWRITING` -> `DOCUMENT_COLLECTION` (Decision: NEED_SALARY_SLIP when limit < amount <= 2x limit)
11. `UNDERWRITING` -> `REJECTION` (Decision: REJECTED when amount > 2x limit)
12. `DOCUMENT_COLLECTION` -> `UNDERWRITING` (Re-runs underwriting when salary slip/salary details are provided)
13. `DOCUMENT_COLLECTION` -> `END` with `TerminalState.CUSTOMER_DROPPED` (Customer declines to provide salary slip, e.g. "I don't have it")

## Terminal Outcomes Coverage Requirements
Verify the 4 terminal states on `ConversationState`:
1. `LOAN_SANCTIONED` (Happy path loan approval)
2. `LOAN_REJECTED` (Low credit score or KYC verification failed)
3. `CUSTOMER_DROPPED` (Declined offer, unregistered customer, or declined document collection)
4. `ADDITIONAL_DOCUMENT_REQUIRED` (Write a test checking that setting it manually returns is_terminal() == True and process_message() triggers the terminal safeguard message: "Conversation ended: ...")

## Scope Boundaries
- Do NOT modify any core files of the POLARIS application (e.g. app.py, master_agent.py, agents/*.py, config.py, mock_apis.py, offer_mart.py, state.py). Only add/edit files in the `tests/` directory.
- DO NOT hardcode test results.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please execute these tests, run pytest to ensure they pass, and write your completion handoff report to `/Users/rishetmehra/Desktop/Findinternships/POLARIS-clone/.agents/worker_fsm/handoff.md`. Include the details of the created test file and the test execution output.
