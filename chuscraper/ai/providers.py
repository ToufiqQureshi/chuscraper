from abc import ABC, abstractmethod
import os
from typing import Any, Dict, List, Optional, Type
import logging

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        json_mode: bool = False
    ) -> str:
        """Generates a text response from the LLM."""
        pass

class GeminiProvider(AIProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types
        except ImportError:
            raise ImportError("Please install 'google-genai' to use modern Gemini features.")
        
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Pass it or set it in environment variables.")
        
        self.client = self.genai.Client(api_key=self.api_key)
        self.model_name = model_name

    async def generate_response(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        json_mode: bool = False
    ) -> str:
        config = None
        if json_mode:
            config = self.types.GenerateContentConfig(
                response_mime_type="application/json",
                system_instruction=system_instruction
            )
        elif system_instruction:
            config = self.types.GenerateContentConfig(
                system_instruction=system_instruction
            )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config
        )
        return response.text

    async def generate_visual_response(
        self, 
        prompt: str, 
        image_bytes: bytes,
        mime_type: str = "image/png"
    ) -> str:
        """Generates a response using vision (multi-modal)."""
        from google.genai import types
        
        content = [
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt
        ]
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=content
        )
        return response.text

class OpenAIProvider(AIProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4o"):
        try:
            from openai import OpenAI
            self.OpenAI = OpenAI
        except ImportError:
            raise ImportError("Please install 'openai' to use OpenAI features.")

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found. Pass it or set it in environment variables.")
        
        self.client = self.OpenAI(api_key=self.api_key)
        self.model_name = model_name

    async def generate_response(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        json_mode: bool = False
    ) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response_format = {"type": "json_object"} if json_mode else None

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            response_format=response_format
        )
        return response.choices[0].message.content or ""
