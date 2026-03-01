import os
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Any
from google import genai
from google.genai import types as genai_types
from openai import OpenAI
from app.services.gemini_retry import retry_gemini_call

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    def generate_content(self, prompt: str, system_prompt: str = "", on_retry: Optional[Callable] = None) -> str:
        pass

class GeminiProvider(LLMProvider):
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        api_key = os.getenv("GOOGLE_API_KEY", "")
        self.client = genai.Client(api_key=api_key) if api_key else None

    def generate_content(self, prompt: str, system_prompt: str = "", on_retry: Optional[Callable] = None) -> str:
        if not self.client:
            raise RuntimeError("GOOGLE_API_KEY not set for GeminiProvider")

        def _call():
            contents = prompt
            if system_prompt:
                contents = f"{system_prompt}

{prompt}"
            
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

    def generate_content(self, prompt: str, system_prompt: str = "", on_retry: Optional[Callable] = None) -> str:
        if not self.client:
            raise RuntimeError("OPENROUTER_API_KEY not set for OpenRouterProvider")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Simplified retry for OpenRouter (can be improved)
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"OpenRouter attempt {attempt+1} failed: {e}")
                if attempt == 2: raise
                import time
                time.sleep(2 ** attempt)
        return ""

def get_llm_provider() -> LLMProvider:
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    model = os.getenv("LLM_MODEL")

    if provider_type == "gemini":
        return GeminiProvider(model=model or "gemini-2.5-flash")
    elif provider_type == "openrouter":
        return OpenRouterProvider(model=model or "anthropic/claude-3.5-sonnet")
    else:
        logger.warning(f"Unknown LLM_PROVIDER '{provider_type}', falling back to Gemini")
        return GeminiProvider()
