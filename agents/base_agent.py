"""
POLARIS Base Agent
Abstract base class for all worker agents.
"""

import json
import hashlib
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from config import get_model


class BaseAgent(ABC):
    """
    Base class for all worker agents.
    Provides Gemini integration and structured output parsing.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.model = get_model()
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass
    
    @abstractmethod
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs and return structured output."""
        pass
    
    def compute_input_hash(self, inputs: Dict[str, Any]) -> str:
        """Compute a hash of inputs for anti-loop tracking."""
        input_str = json.dumps(inputs, sort_keys=True, default=str)
        return hashlib.md5(input_str.encode()).hexdigest()[:8]
    
    def call_llm(self, prompt: str) -> str:
        """Call Gemini LLM with the given prompt."""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise RuntimeError(f"LLM call failed for {self.name}: {str(e)}")
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response.
        Handles markdown code blocks and extracts JSON.
        """
        # Remove markdown code blocks if present
        text = response.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # Try to find JSON in the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Failed to parse JSON from {self.name}: {str(e)}\nResponse: {response[:500]}")
    
    def validate_output(self, output: Dict[str, Any], required_fields: list) -> bool:
        """Validate that all required fields are present in output."""
        for field in required_fields:
            if field not in output:
                return False
        return True
