## 2026-07-02T18:20:13Z
Write a comprehensive test file `tests/test_agents.py` that validates the individual logic and execution of all 4 sub-agents: `SalesAgent`, `VerificationAgent`, `UnderwritingAgent`, and `SanctionAgent`.

Requirements:
Ensure there are test cases verifying:
1. `SalesAgent`:
   - Verifies that `process()` returns a valid dictionary containing `sales_pitch`, `requested_amount`, `tenure_months`, and `purpose`.
   - Tests mock LLM data extraction (e.g., requesting "300000 for 24 months" extracts the correct amount and tenure).
2. `VerificationAgent`:
   - Queries CRM lookup successfully for verified KYC (e.g., Rahul Sharma "9876543210") and check fields are returned.
   - Queries CRM lookup for unverified KYC (e.g., Sneha Reddy "9876543214") and asserts `kyc_verified` is False.
   - Queries CRM lookup for non-existent customer and returns clean failure dict.
3. `UnderwritingAgent`:
   - Verifies rule: Reject if credit score < 700 (e.g. Vikram Singh "9876543213" has credit score 650).
   - Verifies rule: Approve instantly if requested amount <= preapproved limit (e.g., 300,000 for Rahul Sharma).
   - Verifies rule: Set decision to `NEED_SALARY_SLIP` if requested amount is between limit and 2x limit (e.g., 600,000 for Rahul Sharma without salary input).
   - Verifies rule: Approve after income verification if EMI <= 50% salary (e.g., 600,000 for Rahul Sharma with salary 85,000).
   - Verifies rule: Reject after income verification if EMI > 50% salary (e.g., 600,000 for Rahul Sharma with salary 10,000).
   - Verifies rule: Reject if requested amount > 2x limit (e.g., 1,200,000 for Rahul Sharma).
4. `SanctionAgent`:
   - Verifies that calling `process()` generates a unique sanction ID starting with "POLARIS-".
   - Verifies that if `FPDF_AVAILABLE` is True, a physical PDF file is generated in the `sanction_letters/` directory, the dict contains `pdf_generated=True`, and the test clean-up deletes the generated PDF file afterward. If `FPDF_AVAILABLE` is False, verifies the mock output is returned.
