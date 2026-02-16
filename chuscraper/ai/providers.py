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
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types
        except ImportError:
            raise ImportError("Please install 'google-genai' to use modern Gemini features.")
        
        # Support multiple keys for rotation: GEMINI_API_KEYS="key1,key2,key3"
        keys_env = os.environ.get("GEMINI_API_KEYS")
        if keys_env:
            self.api_keys = [k.strip() for k in keys_env.split(",") if k.strip()]
        else:
             # Fallback to single key
             single_key = api_key or os.environ.get("GEMINI_API_KEY")
             if not single_key:
                  raise ValueError("GEMINI_API_KEY not found.")
             self.api_keys = [single_key]

        self.current_key_index = 0
        self.model_name = model_name
        self._init_client()

    def _init_client(self):
        self.client = self.genai.Client(api_key=self.api_keys[self.current_key_index])

    def _rotate_key(self):
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            logger.info(f"🔄 Rotating to API Key #{self.current_key_index + 1}")
            self._init_client()
            return True
        return False

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

        import asyncio
        from google.genai import errors

        max_retries = 3
        
        # Outer loop for key rotation
        for key_attempt in range(len(self.api_keys) * 2): # Try all keys twice
            for attempt in range(max_retries):
                try:
                    response = await asyncio.to_thread(
                        self.client.models.generate_content,
                        model=self.model_name,
                        contents=prompt,
                        config=config
                    )
                    return response.text
                except errors.ClientError as e:
                    error_str = str(e)
                    # 429 = Resource Exhausted
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                         logger.warning(f"⚠️ Gemini Rate Limit (429) on Key #{self.current_key_index+1}")
                         
                         # Try rotating key first
                         if self._rotate_key():
                             break # Break inner retry loop to try new key immediately
                         
                         # If no other keys, backoff
                         if attempt < max_retries - 1:
                            wait_time = (2 ** (attempt + 2)) 
                            logger.info(f"⏳ Retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    # 404 = Model Not Found (maybe key doesn't have access to 2.0)
                    if "404" in error_str or "NOT_FOUND" in error_str:
                         logger.warning(f"❌ Model {self.model_name} not found with current key.")
                         # Fallback to stable model?
                         if self.model_name != "gemini-1.5-flash":
                             logger.info("⬇️ Downgrading to 'gemini-1.5-flash'...")
                             self.model_name = "gemini-1.5-flash"
                             continue

                    raise e
        
        raise RuntimeError("All API keys and retries exhausted. Please check your quota.")

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

class OllamaProvider(AIProvider):
    def __init__(self, base_url: str = "http://localhost:11434/v1", model_name: str = "llama3"):
        """
        Uses Ollama's OpenAI-compatible API.
        Ensure Ollama is running with OLLAMA_HOST=0.0.0.0 (if remote) or just local defaults.
        """
        try:
            from openai import OpenAI
            self.OpenAI = OpenAI
        except ImportError:
            raise ImportError("Please install 'openai' to use Ollama via its OpenAI-compatible API.")

        # Ollama doesn't usually need an API key, so we use a dummy one
        self.client = self.OpenAI(
            base_url=base_url,
            api_key="ollama"
        )
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

        # Note: Ollama handles json_mode if the model supports it and prompt asks for it.
        # We pass it to the OpenAI-compatible client.
        response_format = {"type": "json_object"} if json_mode else None

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format=response_format
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Ollama Error: {e}")
            return f"Error connecting to Ollama: {e}"
