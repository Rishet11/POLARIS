## 2026-07-02T18:16:31Z
You are a Test Setup Developer (Worker) for the POLARIS test suite.
Your working directory is /Users/rishetmehra/Desktop/Findinternships/POLARIS-clone/.agents/worker_setup/.
Please create all coordinates under /Users/rishetmehra/Desktop/Findinternships/POLARIS-clone/.agents/worker_setup/.

## Objective
Establish the testing framework using pytest and implement Gemini LLM mocking utilities so that tests can run and import application code offline without requiring a real API key.

## Requirements
1. Create a `tests/conftest.py` file at the root. In this file, set `os.environ["GOOGLE_API_KEY"] = "mock_api_key_for_testing"` to bypass the `config.py` key validation check.
2. In `tests/conftest.py`, mock `google.generativeai` (e.g. using `sys.modules`) or construct a mock fixture for the model returned by `config.get_model()`. The mock model's `generate_content` method must return a mock response containing a `text` attribute with custom JSON outputs based on what agent is calling it.
3. Write a sanity test `tests/test_sanity.py` that instantiates `MasterAgent` and simulates a basic message processing call (e.g., greeting) to verify that imports and model mocking work.
4. Run the sanity test using `pytest` to verify it passes.

## Scope Boundaries
- Do NOT modify any core files of the POLARIS application (e.g., app.py, master_agent.py, agents/*.py, config.py, mock_apis.py, offer_mart.py, state.py). Only add/edit files in the `tests/` directory.
- DO NOT hardcode test results in the application itself.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please execute this setup, run the test, and write your completion handoff report to `/Users/rishetmehra/Desktop/Findinternships/POLARIS-clone/.agents/worker_setup/handoff.md`. Include the details of the created files and the test execution output.
