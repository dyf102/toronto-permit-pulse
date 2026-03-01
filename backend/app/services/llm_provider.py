import os
import logging
from abc import ABC, abstractmethod
from typing import Callable, Any
from google import genai
from google.genai import types as genai_types
from openai import OpenAI
from app.services.gemini_retry import retry_gemini_call

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    def generate_content(self, prompt: str, system_prompt: str = "", on_retry: Callable[[int, float, str], None] | None = None) -> str:
        pass

class GeminiProvider(LLMProvider):
    def __init__(self, model: str = "gemini-3-flash-preview"):
        self.model = model
        api_key = os.getenv("GOOGLE_API_KEY", "")
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        
        # Partner models like Claude 4.6 on Vertex AI require project_id and vertexai=True
        # Native Gemini models should use API_KEY only (or ADC)
        if "claude" in model.lower():
            if not project_id:
                raise RuntimeError(f"GOOGLE_CLOUD_PROJECT must be set to use partner model: {model}")
            
            self.client = genai.Client(
                project=project_id,
                location="us-east5", # Default location for Claude on Vertex
                vertexai=True
            )
        else:
            self.client = genai.Client(api_key=api_key) if api_key else None

    def generate_content(self, prompt: str, system_prompt: str = "", on_retry: Callable[[int, float, str], None] | None = None) -> str:
        if not self.client:
            raise RuntimeError("GOOGLE_API_KEY not set for GeminiProvider")

        def _call():
            contents = prompt
            if system_prompt:
                contents = f"{system_prompt}\\n\\n{prompt}"
            
            return self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=genai_types.GenerateContentConfig(temperature=0.1),
            )

        response = retry_gemini_call(
            _call,
            on_retry=on_retry
        )
        return response.text.strip()

class OpenRouterProvider(LLMProvider):
    def __init__(self, model: str = "anthropic/claude-3-haiku"):
        self.model = model
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        ) if api_key else None

    def generate_content(self, prompt: str, system_prompt: str = "", on_retry: Callable[[int, float, str], None] | None = None) -> str:
        if not self.client:
            raise RuntimeError("OPENROUTER_API_KEY not set for OpenRouterProvider")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Simplified retry for OpenRouter (can be improved)
        # In development mode, retries are disabled to fail fast.
        max_attempts = 1 if os.getenv("ENVIRONMENT") == "development" else 3
        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"OpenRouter attempt {attempt+1} failed: {e}")
                if attempt == max_attempts - 1: raise
                import time
                time.sleep(2 ** attempt)
        return ""

def get_llm_provider() -> LLMProvider:
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    model = os.getenv("LLM_MODEL")

    if provider_type == "gemini":
        # Supports native Gemini and Vertex partner models like claude-opus-4-6
        return GeminiProvider(model=model or "gemini-3-flash-preview")
    elif provider_type == "openrouter":
        return OpenRouterProvider(model=model or "anthropic/claude-3.5-sonnet")
    else:
        logger.warning(f"Unknown LLM_PROVIDER '{provider_type}', falling back to Gemini")
        return GeminiProvider()
