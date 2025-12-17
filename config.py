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

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

# Configure Gemini
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

# Create model instance
def get_model():
    """Get configured Gemini model instance."""
    return genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS,
    )

# System constants
MAX_AGENT_CALLS = 6  # Maximum agent calls per conversation
TERMINAL_STATES = ["LOAN_SANCTIONED", "LOAN_REJECTED", "ADDITIONAL_DOCUMENT_REQUIRED", "CUSTOMER_DROPPED"]
