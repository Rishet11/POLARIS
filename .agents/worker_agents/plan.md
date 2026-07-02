# Test Development Plan for POLARIS Agent Logic

We need to create `tests/test_agents.py` to validate the logic of all four sub-agents: `SalesAgent`, `VerificationAgent`, `UnderwritingAgent`, and `SanctionAgent`.

## Steps

1. **Verify workspace and imports**: Ensure we can import all agent classes and helper utilities.
2. **Draft SalesAgent Tests**:
   - `test_sales_agent_process_format`: Check output dict structure matches `{sales_pitch, requested_amount, tenure_months, purpose}`.
   - `test_sales_agent_data_extraction`: Validate extraction of amount and tenure from conversation message (e.g. "300000 for 24 months") using the mocked LLM environment.
3. **Draft VerificationAgent Tests**:
   - `test_verification_agent_verified_kyc`: Query Rahul Sharma ("9876543210"), assert `kyc_verified` is True and verify all returned profile and offer fields.
   - `test_verification_agent_unverified_kyc`: Query Sneha Reddy ("9876543214"), assert `kyc_verified` is False.
   - `test_verification_agent_non_existent`: Query non-existent phone (e.g. "9999999999"), verify clean failure dict response.
4. **Draft UnderwritingAgent Tests**:
   - `test_underwriting_agent_low_credit_score`: Reject if credit score < 700 (Vikram Singh "9876543213", score 650).
   - `test_underwriting_agent_approve_instantly`: Approve instantly if amount <= preapproved limit (Rahul Sharma 300k vs 500k limit).
   - `test_underwriting_agent_need_salary_slip`: Set decision to `NEED_SALARY_SLIP` if amount is between limit and 2x limit (Rahul Sharma 600k vs 500k limit, no salary).
   - `test_underwriting_agent_approve_with_salary`: Approve after salary verification if EMI <= 50% salary (Rahul Sharma 600k with 85,000 salary).
   - `test_underwriting_agent_reject_due_to_salary`: Reject after salary verification if EMI > 50% salary (Rahul Sharma 600k with 10,000 salary).
   - `test_underwriting_agent_reject_above_double_limit`: Reject if amount > 2x limit (Rahul Sharma 1,200,000 vs 500k limit).
5. **Draft SanctionAgent Tests**:
   - `test_sanction_agent_fpdf_enabled`: If FPDF is available, verify unique ID starts with "POLARIS-", PDF is created under `sanction_letters/`, `pdf_generated=True`, and clean up deleted PDF file.
   - `test_sanction_agent_fpdf_disabled`: If FPDF is mock-disabled, verify unique ID starts with "POLARIS-", PDF is not generated, and mock details are returned.
6. **Run Pytest**: Execute `PYTHONPATH=. pytest tests/test_agents.py` and verify all tests pass.
7. **Write Handoff Report**: Record details of findings and results in `handoff.md`.
