import httpx
import os
import json
from typing import Dict, Any
from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()

class PromptExecutor:
    def __init__(self, api_key=None):
        # Use the provided API key or get from environment
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("No ANTHROPIC_API_KEY found in environment")
        
        # Initialize the Anthropic client
        self.client = Anthropic(api_key=self.api_key)
    
    async def execute_prompt(self, prompt_text: str) -> str:
        """Execute a prompt using Anthropic's Claude API"""
        response = await self.client.messages.create(
            model="claude-3-5-haiku-20240307",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.0,  # Lower temperature for more deterministic outputs
            system="You are a TypeScript expert that translates OpenAPI/Swagger schemas to TypeScript DTOs. Your responses are clean, well-formatted TypeScript code only."
        )
        
        return response.content[0].text