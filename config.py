"""
POLARIS Configuration Module
Handles Gemini API setup and global configuration.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Demo mode: no API key needed, canned LLM responses (for hosted demos)
DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes") or not GOOGLE_API_KEY

if not DEMO_MODE:
    genai.configure(api_key=GOOGLE_API_KEY)

# Model Configuration
MODEL_NAME = "gemini-2.0-flash"

# Generation settings for deterministic outputs
GENERATION_CONFIG = {
    "temperature": 0.1,  # Low temperature for consistency
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 1024,
}

# Safety settings - permissive for business conversations
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

class _DemoResponse:
    def __init__(self, text):
        self.text = text


class _DemoModel:
    """Keyless stand-in for Gemini used in DEMO_MODE.

    Mirrors the SalesAgent JSON contract so the origination flow works
    end-to-end without an API key; other prompts get a generic reply.
    """

    def generate_content(self, prompt, **kwargs):
        import json
        import re

        prompt_lower = prompt.lower()
        if "sales" in prompt_lower or "charismatic" in prompt_lower:
            customer_part = prompt
            if "customer message:" in prompt_lower:
                customer_part = prompt.split("CUSTOMER MESSAGE:")[-1]
            numbers = [int(n) for n in re.findall(r"\d+", customer_part)]
            requested_amount = numbers[0] if numbers else 300000
            tenure_months = numbers[1] if len(numbers) >= 2 else 24
            return _DemoResponse(json.dumps({
                "sales_pitch": (
                    f"₹{requested_amount:,} over {tenure_months} months is a solid choice. "
                    "Let's get your verification done right away!"
                ),
                "requested_amount": requested_amount,
                "tenure_months": tenure_months,
                "purpose": "personal",
            }))
        return _DemoResponse(
            "Thanks for your message. Let's continue with your application."
        )


# Create model instance
def get_model():
    """Get configured Gemini model instance (or demo stand-in)."""
    if DEMO_MODE:
        return _DemoModel()
    return genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS,
    )

# System constants
MAX_AGENT_CALLS = 6  # Maximum agent calls per conversation
TERMINAL_STATES = ["LOAN_SANCTIONED", "LOAN_REJECTED", "ADDITIONAL_DOCUMENT_REQUIRED", "CUSTOMER_DROPPED"]
