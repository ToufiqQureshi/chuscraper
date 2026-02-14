import json
from typing import Any, Dict, Optional, Type
try:
    from pydantic import BaseModel
except ImportError:
    class BaseModel: pass

class AISchemaHandler:
    @staticmethod
    def wrap_prompt(prompt: str, schema: Optional[Type[BaseModel]] = None) -> str:
        """Wraps the user prompt with instruction for JSON output based on schema."""
        if not schema:
            return prompt
            
        schema_json = ""
        if hasattr(schema, "model_json_schema"): # Pydantic v2
             schema_json = json.dumps(schema.model_json_schema(), indent=2)
        elif hasattr(schema, "schema"): # Pydantic v1
             schema_json = json.dumps(schema.schema(), indent=2)
             
        instruction = f"""
Extract data from the following text based on this request: "{prompt}"

CRITICAL: Return ONLY valid JSON that matches this schema:
{schema_json}

If a field is not found, use null. do not invent data.
"""
        return instruction

    @staticmethod
    def validate_and_parse(response_text: str, schema: Type[BaseModel]) -> Any:
        """Parses the JSON response and validates it against the Pydantic schema."""
        # Clean potential markdown code blocks
        clean_json = response_text
        if "```json" in response_text:
            clean_json = response_text.split("```json")[-1].split("```")[0].strip()
        elif "```" in response_text:
            clean_json = response_text.split("```")[-1].split("```")[0].strip()
            
        data = json.loads(clean_json)
        return schema(**data)
