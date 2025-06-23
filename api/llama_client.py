import httpx
import asyncio
import time
from typing import Dict, Any, Optional
from .config import LlamaConfig
from .models import ChatCompletionRequest
import structlog

logger = structlog.get_logger()

class LlamaClient:
    def __init__(self, config: LlamaConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.timeout)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"{self.config.endpoint}/health")
            response.raise_for_status()
            return {
                "status": "healthy",
                "endpoint": self.config.endpoint,
                "response_time": response.elapsed.total_seconds()
            }
        except httpx.RequestError as e:
            logger.error("Health check failed", error=str(e), endpoint=self.config.endpoint)
            return {
                "status": "unhealthy",
                "endpoint": self.config.endpoint,
                "error": str(e)
            }
        except httpx.HTTPStatusError as e:
            logger.error("Health check HTTP error", status_code=e.response.status_code, endpoint=self.config.endpoint)
            return {
                "status": "unhealthy",
                "endpoint": self.config.endpoint,
                "error": f"HTTP {e.response.status_code}"
            }
    
    async def generate(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        prompt_text = request.get_prompt_text()
        
        payload = {
            "prompt": prompt_text,
            "n_predict": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "top_k": request.top_k,
            "repeat_penalty": request.repeat_penalty,
            "stop": request.stop if isinstance(request.stop, list) else [request.stop] if request.stop else [],
            "stream": False,
            "cache_prompt": True
        }
        
        start_time = time.time()
        
        for attempt in range(self.config.max_retries):
            try:
                logger.info("Sending generation request", 
                           attempt=attempt + 1, 
                           max_retries=self.config.max_retries,
                           prompt_length=len(prompt_text))
                
                response = await self.client.post(
                    f"{self.config.endpoint}/completion",
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                generation_time = time.time() - start_time
                
                logger.info("Generation completed", 
                           generation_time=generation_time,
                           tokens_predicted=result.get("tokens_predicted", 0))
                
                return {
                    "content": result.get("content", ""),
                    "tokens_predicted": result.get("tokens_predicted", 0),
                    "tokens_evaluated": result.get("tokens_evaluated", 0),
                    "generation_time": generation_time,
                    "tokens_per_second": result.get("tokens_predicted", 0) / generation_time if generation_time > 0 else 0,
                    "truncated": result.get("truncated", False),
                    "stop_reason": result.get("stop", "length")
                }
                
            except httpx.RequestError as e:
                logger.warning("Request failed", 
                              attempt=attempt + 1, 
                              error=str(e),
                              will_retry=attempt < self.config.max_retries - 1)
                
                if attempt == self.config.max_retries - 1:
                    raise Exception(f"Failed to connect to llama.cpp server after {self.config.max_retries} attempts: {e}")
                
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except httpx.HTTPStatusError as e:
                logger.error("HTTP error from llama.cpp server", 
                            status_code=e.response.status_code, 
                            response_text=e.response.text)
                raise Exception(f"HTTP {e.response.status_code} from llama.cpp server: {e.response.text}")
        
        raise Exception("Unexpected error: maximum retries exceeded without raising an exception")