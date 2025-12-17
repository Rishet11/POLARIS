"""
POLARIS Sanction Letter Generator
Generates sanction letters for approved loans.
"""

import os
import uuid
from datetime import datetime
from typing import Any, Dict
from .base_agent import BaseAgent

# Try to import FPDF, but don't fail if not available
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


class SanctionAgent(BaseAgent):
    """
    Sanction Letter Generator Agent.
    
    Trigger: Only when decision == APPROVED
    Output: {pdf_generated, sanction_id, pdf_path}
    
    Generates a formal sanction letter PDF.
    """
    
    def __init__(self):
        super().__init__("SANCTION_LETTER_GENERATOR")
        self.output_dir = "sanction_letters"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_system_prompt(self) -> str:
        # Not used as this agent generates documents
        return ""
    
    def generate_sanction_id(self) -> str:
        """Generate unique sanction ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_suffix = uuid.uuid4().hex[:6].upper()
        return f"POLARIS-{timestamp}-{unique_suffix}"
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate sanction letter.
        
        Args:
            inputs: {
                customer_name: str,
                customer_id: str,
                approved_amount: float,
                tenure_months: int,
                interest_rate: float,
                emi: float
            }
        
        Returns:
            {pdf_generated: bool, sanction_id: str, pdf_path: str (if generated)}
        """
        customer_name = inputs.get("customer_name", "Customer")
        customer_id = inputs.get("customer_id", "N/A")
        approved_amount = inputs.get("approved_amount", 0)
        tenure_months = inputs.get("tenure_months", 12)
        interest_rate = inputs.get("interest_rate", 14.0)
        emi = inputs.get("emi", 0)
        
        sanction_id = self.generate_sanction_id()
        
        if not FPDF_AVAILABLE:
            # Return mock response if FPDF not installed
            return {
                "pdf_generated": False,
                "sanction_id": sanction_id,
                "pdf_path": None,
                "message": "Sanction letter generated (PDF library not available)",
                "details": {
                    "customer_name": customer_name,
                    "customer_id": customer_id,
                    "approved_amount": approved_amount,
                    "tenure_months": tenure_months,
                    "interest_rate": interest_rate,
                    "emi": emi,
                    "sanction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        
        # Generate PDF
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # Header
            pdf.set_font("Arial", "B", 20)
            pdf.cell(0, 15, "POLARIS NBFC", ln=True, align="C")
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "LOAN SANCTION LETTER", ln=True, align="C")
            pdf.ln(10)
            
            # Sanction ID and Date
            pdf.set_font("Arial", "", 11)
            pdf.cell(0, 8, f"Sanction ID: {sanction_id}", ln=True)
            pdf.cell(0, 8, f"Date: {datetime.now().strftime('%B %d, %Y')}", ln=True)
            pdf.ln(10)
            
            # Customer Details
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "Dear " + customer_name + ",", ln=True)
            pdf.ln(5)
            
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 8, 
                f"We are pleased to inform you that your personal loan application has been APPROVED. "
                f"Please find the details of your sanctioned loan below:"
            )
            pdf.ln(10)
            
            # Loan Details Table
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "LOAN DETAILS", ln=True)
            pdf.set_font("Arial", "", 11)
            
            details = [
                ("Customer ID", customer_id),
                ("Sanctioned Amount", f"Rs. {approved_amount:,.2f}"),
                ("Interest Rate", f"{interest_rate}% per annum"),
                ("Tenure", f"{tenure_months} months"),
                ("Monthly EMI", f"Rs. {emi:,.2f}"),
                ("Total Repayment", f"Rs. {emi * tenure_months:,.2f}"),
            ]
            
            for label, value in details:
                pdf.cell(80, 8, label + ":", border=1)
                pdf.cell(0, 8, str(value), border=1, ln=True)
            
            pdf.ln(15)
            
            # Terms
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "TERMS & CONDITIONS", ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(0, 6, 
                "1. The loan amount will be disbursed to your registered bank account within 24 hours.\n"
                "2. EMI will be auto-debited from your account on the 5th of every month.\n"
                "3. Prepayment is allowed after 6 EMIs with no prepayment charges.\n"
                "4. Late payment will attract a penalty of 2% per month on the overdue amount.\n"
                "5. This sanction is valid for 30 days from the date of issue."
            )
            
            pdf.ln(15)
            
            # Signature
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, "Authorized Signatory", ln=True)
            pdf.set_font("Arial", "", 11)
            pdf.cell(0, 8, "POLARIS NBFC", ln=True)
            
            # Save PDF
            pdf_filename = f"{sanction_id}.pdf"
            pdf_path = os.path.join(self.output_dir, pdf_filename)
            pdf.output(pdf_path)
            
            return {
                "pdf_generated": True,
                "sanction_id": sanction_id,
                "pdf_path": pdf_path,
                "message": "Sanction letter generated successfully",
                "details": {
                    "customer_name": customer_name,
                    "customer_id": customer_id,
                    "approved_amount": approved_amount,
                    "tenure_months": tenure_months,
                    "interest_rate": interest_rate,
                    "emi": emi,
                    "sanction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
        except Exception as e:
            return {
                "pdf_generated": False,
                "sanction_id": sanction_id,
                "pdf_path": None,
                "error": str(e),
                "message": "Failed to generate PDF sanction letter"
            }
