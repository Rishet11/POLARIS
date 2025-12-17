"""
POLARIS Sales Agent
Extracts loan request details from customer intent.
"""

from typing import Any, Dict
from .base_agent import BaseAgent


class SalesAgent(BaseAgent):
    """
    Sales Agent for extracting loan requirements.
    
    Input: Customer intent (natural language)
    Output: {requested_amount, tenure_months, justification_summary}
    
    Rules:
    - Deterministic extraction only
    - No persuasion or conversation
    - Single-call policy
    """
    
    def __init__(self):
        super().__init__("SALES_AGENT")
    
    def get_system_prompt(self) -> str:
        return """You are a LOAN REQUIREMENT EXTRACTION AGENT. Your ONLY job is to extract structured data from customer messages.

RULES:
1. Extract ONLY these fields from the customer's message:
   - requested_amount: The loan amount in INR (number only, no currency symbols)
   - tenure_months: The loan tenure in months (number only)
   - purpose: Brief reason for the loan (if mentioned)

2. If a field is NOT mentioned, set it to null.

3. Output ONLY valid JSON in this exact format:
{
    "requested_amount": <number or null>,
    "tenure_months": <number or null>,
    "purpose": "<string or null>",
    "justification_summary": "<brief summary of what customer wants>"
}

4. DO NOT:
   - Add any text before or after the JSON
   - Ask questions
   - Make assumptions about missing values
   - Include currency symbols or text in numbers

EXAMPLES:

Input: "I need a loan of 5 lakhs for 3 years to renovate my home"
Output:
{
    "requested_amount": 500000,
    "tenure_months": 36,
    "purpose": "home renovation",
    "justification_summary": "Customer wants 5 lakh loan for 36 months for home renovation"
}

Input: "I want to take a personal loan"
Output:
{
    "requested_amount": null,
    "tenure_months": null,
    "purpose": null,
    "justification_summary": "Customer wants a personal loan but did not specify amount or tenure"
}

Input: "50000 rupees loan"
Output:
{
    "requested_amount": 50000,
    "tenure_months": null,
    "purpose": null,
    "justification_summary": "Customer wants 50,000 rupees loan, tenure not specified"
}"""
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract loan requirements from customer message.
        
        Args:
            inputs: {"customer_message": str, "conversation_context": str (optional)}
        
        Returns:
            {requested_amount, tenure_months, purpose, justification_summary}
        """
        customer_message = inputs.get("customer_message", "")
        context = inputs.get("conversation_context", "")
        
        prompt = f"""{self.get_system_prompt()}

CONVERSATION CONTEXT:
{context if context else "No prior context"}

CUSTOMER MESSAGE:
{customer_message}

Extract the loan requirements and respond with ONLY the JSON:"""
        
        response = self.call_llm(prompt)
        result = self.parse_json_response(response)
        
        # Validate output
        required_fields = ["requested_amount", "tenure_months", "justification_summary"]
        if not self.validate_output(result, required_fields):
            result.setdefault("requested_amount", None)
            result.setdefault("tenure_months", None)
            result.setdefault("purpose", None)
            result.setdefault("justification_summary", "Unable to extract requirements")
        
        return result
