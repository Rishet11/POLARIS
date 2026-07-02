## 2026-07-02T18:23:53Z

You are an Integration Developer (Worker) for the POLARIS test suite.
Your working directory is /Users/rishetmehra/Desktop/Findinternships/POLARIS-clone/.agents/worker_integration/.
Please create all coordinates under /Users/rishetmehra/Desktop/Findinternships/POLARIS-clone/.agents/worker_integration/.

## Objective
Verify the complete POLARIS test suite by running all test files together using pytest, asserting 100% pass rate, and verifying that the suite runs completely offline without any real Gemini API keys.

## Requirements
1. Run the entire test suite from the project root using:
   ```bash
   PYTHONPATH=. pytest
   ```
2. Verify that:
   - All tests in `tests/test_sanity.py`, `tests/test_fsm.py`, `tests/test_agents.py`, and `tests/test_safeguards.py` pass.
   - The test run does not request any external API calls and requires no real API keys.
3. Check if there are any warnings or logs indicating cheating or hardcoding.
4. Document the full command output in your handoff report at `/Users/rishetmehra/Desktop/Findinternships/POLARIS-clone/.agents/worker_integration/handoff.md`.

## Scope Boundaries
- Do NOT modify any core files of the POLARIS application (e.g. app.py, master_agent.py, agents/*.py, config.py, mock_apis.py, offer_mart.py, state.py). Only run tests and verify.
- DO NOT hardcode test results.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please execute the test suite, verify the output, and write your completion handoff report.
