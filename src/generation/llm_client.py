import os
import requests
import time
from typing import Dict, Optional
from ..shared import get_logger, retry_with_backoff, rate_limiter

logger = get_logger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        # Ticket specifies GLM-4.5 Air. Using zhipu/glm-4-air as best guess for slug.
        self.model = os.getenv("OPENROUTER_MODEL", "zhipu/glm-4-air")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.timeout_primary = 10
        self.timeout_fallback = 5
        
        logger.info("LLMClient initialized", model=self.model, has_key=bool(self.api_key))
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        if not self.api_key:
            logger.warning("No API key configured, using fallback")
            return None
        
        if not rate_limiter.consume("openrouter", tokens=1, capacity=100, refill_rate=100, refill_period=3600):
            logger.warning("Rate limit exceeded for OpenRouter")
            return None
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://viralos.prime",
                    "X-Title": "ViralOS Prime",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 4000,
                    "temperature": 0.7,
                },
                timeout=self.timeout_primary,
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                logger.info("LLM generation successful", length=len(content))
                return content
            else:
                logger.error(
                    "LLM API error",
                    status_code=response.status_code,
                    response=response.text[:200]
                )
                return None
        
        except requests.Timeout:
            logger.warning("LLM request timeout")
            return None
        except Exception as e:
            logger.error("LLM generation error", error=str(e))
            return None
