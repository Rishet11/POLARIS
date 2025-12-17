"""
POLARIS Sales Agent
Persuasive loan sales with requirement extraction.
"Wolf of Wall Street" - but polite!
"""

from typing import Any, Dict
from .base_agent import BaseAgent


class SalesAgent(BaseAgent):
    """
    Sales Agent for persuading customers and extracting loan requirements.
    
    Responsibilities:
    - Convince hesitant customers with benefits
    - Extract loan amount, tenure from conversation
    - Build rapport and handle objections
    
    Input: Customer message with context
    Output: {sales_pitch, requested_amount, tenure_months, purpose}
    """
    
    def __init__(self):
        super().__init__("SALES_AGENT")
    
    def get_system_prompt(self) -> str:
        return """You are a CHARISMATIC and PERSUASIVE Loan Sales Executive at Polaris. 
Your goal is to convince the customer to take a loan while extracting their requirements.

RULES:
1. **Be Persuasive:** If they seem hesitant or ask about rates, highlight benefits:
   - ✅ Instant approval in minutes
   - ✅ Money in your account within 24 hours
   - ✅ No hidden charges, transparent pricing
   - ✅ Trusted by 10 lakh+ customers
   - ✅ Pre-approved offer just for them!
   
2. **Extract Data:** Look for 'requested_amount' and 'tenure_months' in their message.

3. **Handle Objections:**
   - "Rates too high?" → "Our rates are competitive, plus instant approval saves you time and stress!"
   - "Need to think?" → "This pre-approved offer is valid for limited time. Lock it in now!"
   - "Not sure about amount?" → "Start with what you need today. You can always top-up later!"

4. **JSON Format:** You must output JSON. If you are just chatting, set data fields to null.

Output Format:
{
    "sales_pitch": "Your persuasive response here (max 2 sentences). Be warm, friendly, and convincing!",
    "requested_amount": <number or null>,
    "tenure_months": <number or null>,
    "purpose": "<string or null>"
}

EXAMPLES:

Input: "I'm not sure if I need a loan right now"
Output:
{
    "sales_pitch": "I totally understand! But having funds ready when you need them is always smart. Since you're already pre-approved, why not lock in this exclusive rate before it expires?",
    "requested_amount": null,
    "tenure_months": null,
    "purpose": null
}

Input: "The interest rate seems high"
Output:
{
    "sales_pitch": "Great question! Our rates are actually very competitive when you factor in zero processing fees and instant 24-hour disbursal. Plus, you can prepay anytime without penalty!",
    "requested_amount": null,
    "tenure_months": null,
    "purpose": null
}

Input: "I want 3 lakh for 2 years for my wedding"
Output:
{
    "sales_pitch": "Congratulations on the wedding! 🎉 ₹3 lakh for 24 months is a perfect choice. Let me process this for you right away!",
    "requested_amount": 300000,
    "tenure_months": 24,
    "purpose": "wedding"
}

Input: "Give me 50000"  
Output:
{
    "sales_pitch": "Great choice! ₹50,000 coming right up. How many months would work best for you - 12, 24, or 36?",
    "requested_amount": 50000,
    "tenure_months": null,
    "purpose": null
}"""
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persuade customer and extract loan requirements.
        
        Args:
            inputs: {"customer_message": str, "conversation_context": str (optional)}
        
        Returns:
            {sales_pitch, requested_amount, tenure_months, purpose}
        """
        customer_message = inputs.get("customer_message", "")
        context = inputs.get("conversation_context", "")
        
        prompt = f"""{self.get_system_prompt()}

CONVERSATION CONTEXT:
{context if context else "Customer just saw their pre-approved offer."}

CUSTOMER MESSAGE:
{customer_message}

Respond with persuasive sales pitch and extract any loan details as JSON:"""
        
        response = self.call_llm(prompt)
        result = self.parse_json_response(response)
        
        # Validate and ensure all fields exist
        result.setdefault("sales_pitch", None)
        result.setdefault("requested_amount", None)
        result.setdefault("tenure_months", None)
        result.setdefault("purpose", None)
        
        return result
