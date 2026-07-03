"""
conftest.py - Pytest configuration and LLM mocking.
Sets up the environment and mocks the Gemini API for offline testing.
"""

import os
import sys
from unittest.mock import MagicMock

# 1. Set GOOGLE_API_KEY environment variable to bypass config validation check
os.environ["GOOGLE_API_KEY"] = "mock_api_key_for_testing"

# 2. Construct a mock response class with a text attribute containing custom JSON
class MockResponse:
    def __init__(self, text):
        self.text = text

# 3. Construct a mock GenerativeModel
class MockGenerativeModel:
    def __init__(self, model_name=None, generation_config=None, safety_settings=None):
        self.model_name = model_name
        self.generation_config = generation_config
        self.safety_settings = safety_settings

    def generate_content(self, prompt, **kwargs):
        """
        Returns mock JSON response based on the agent type or prompt context.
        """
        import json
        
        prompt_lower = prompt.lower()
        
        # Check if the prompt is for the SalesAgent
        if "sales" in prompt_lower or "charismatic" in prompt_lower:
            # Isolate the customer message to avoid matching system prompt examples
            customer_part = prompt
            if "customer message:" in prompt_lower:
                customer_part = prompt.split("CUSTOMER MESSAGE:")[-1]
            
            # Default values
            requested_amount = 300000
            tenure_months = 24
            
            # Extract numbers from the customer part using regex
            import re
            numbers = [int(n) for n in re.findall(r'\d+', customer_part)]
            if numbers:
                if len(numbers) >= 1:
                    requested_amount = numbers[0]
                if len(numbers) >= 2:
                    tenure_months = numbers[1]
                
            res_data = {
                "sales_pitch": f"Excellent! ₹{requested_amount:,} for {tenure_months} months is a perfect choice. Let's proceed with verification right away!",
                "requested_amount": requested_amount,
                "tenure_months": tenure_months,
                "purpose": "wedding"
            }
            return MockResponse(json.dumps(res_data))
        
        # Default fallback response for other agents if they call LLM
        res_data = {
            "sales_pitch": "Hello, how can I assist you with your loan today?",
            "requested_amount": None,
            "tenure_months": None,
            "purpose": None
        }
        return MockResponse(json.dumps(res_data))

# 4. Mock ONLY google.generativeai, keeping the real google namespace package
# intact (google.protobuf is needed by streamlit's test framework).
import types
import google as google_mod

genai_mod = types.ModuleType("google.generativeai")
genai_mod.configure = lambda *args, **kwargs: None
genai_mod.GenerativeModel = MockGenerativeModel

google_mod.generativeai = genai_mod
sys.modules['google.generativeai'] = genai_mod

