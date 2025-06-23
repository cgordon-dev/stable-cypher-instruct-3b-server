from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from typing import Optional, Literal
import os

class LlamaConfig(BaseModel):
    endpoint: str = Field(..., description="Llama.cpp server endpoint")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    
    @validator('endpoint')
    def validate_endpoint(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Endpoint must start with http:// or https://')
        return v

class APIConfig(BaseModel):
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    max_tokens: int = Field(default=512, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
    
class MonitoringConfig(BaseModel):
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=8001, description="Port for metrics endpoint")

class Settings(BaseSettings):
    llama_endpoint: str = Field(default="http://localhost:8080", env="LLAMA_ENDPOINT")
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO", env="LOG_LEVEL")
    
    max_tokens: int = Field(default=512, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    top_p: float = Field(default=0.9, env="TOP_P")
    
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8001, env="METRICS_PORT")
    
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @validator('llama_endpoint')
    def validate_llama_endpoint(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('LLAMA_ENDPOINT must start with http:// or https://')
        return v
    
    @property
    def llama_config(self) -> LlamaConfig:
        return LlamaConfig(
            endpoint=self.llama_endpoint,
            timeout=self.request_timeout,
            max_retries=self.max_retries
        )
    
    @property
    def api_config(self) -> APIConfig:
        return APIConfig(
            api_key=self.api_key,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p
        )
    
    @property
    def monitoring_config(self) -> MonitoringConfig:
        return MonitoringConfig(
            enable_metrics=self.enable_metrics,
            metrics_port=self.metrics_port
        )

settings = Settings()