from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import uuid
from datetime import datetime
import structlog

from .config import settings
from .models import (
    ChatCompletionRequest, 
    ChatCompletionResponse, 
    ChatCompletionChoice,
    ChatMessage,
    Role,
    Usage,
    HealthResponse,
    ErrorResponse
)
from .llama_client import LlamaClient
from .metrics import metrics_middleware, get_metrics

logger = structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
).get_logger()

llama_client: LlamaClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llama_client
    logger.info("Starting API server", llama_endpoint=settings.llama_endpoint)
    
    llama_client = LlamaClient(settings.llama_config)
    
    health = await llama_client.health_check()
    if health["status"] != "healthy":
        logger.error("Failed to connect to llama.cpp server", health=health)
        raise Exception(f"Cannot connect to llama.cpp server: {health.get('error')}")
    
    logger.info("Successfully connected to llama.cpp server", health=health)
    yield
    
    if llama_client:
        await llama_client.client.aclose()
    logger.info("API server shutdown complete")

app = FastAPI(
    title="Stable Cypher Instruct API",
    description="FastAPI wrapper for stable-cypher-instruct-3b model via llama.cpp",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.monitoring_config.enable_metrics:
    app.middleware("http")(metrics_middleware)

security = HTTPBearer(auto_error=False)

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if settings.api_config.api_key:
        if not credentials or credentials.credentials != settings.api_config.api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True

@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        llama_health = await llama_client.health_check()
        
        return HealthResponse(
            status="healthy" if llama_health["status"] == "healthy" else "degraded",
            timestamp=datetime.utcnow().isoformat(),
            llama_server=llama_health
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Health check failed: {e}")

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    _: bool = Depends(verify_api_key)
):
    try:
        logger.info("Processing chat completion request", 
                   has_messages=bool(request.messages),
                   has_prompt=bool(request.prompt),
                   max_tokens=request.max_tokens)
        
        start_time = time.time()
        result = await llama_client.generate(request)
        
        completion_id = str(uuid.uuid4())
        created_timestamp = int(time.time())
        
        response = ChatCompletionResponse(
            id=completion_id,
            created=created_timestamp,
            model="stable-cypher-instruct-3b",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role=Role.ASSISTANT,
                        content=result["content"]
                    ),
                    finish_reason=result.get("stop_reason", "length")
                )
            ],
            usage=Usage(
                prompt_tokens=result.get("tokens_evaluated", 0),
                completion_tokens=result.get("tokens_predicted", 0),
                total_tokens=result.get("tokens_evaluated", 0) + result.get("tokens_predicted", 0)
            )
        )
        
        total_time = time.time() - start_time
        logger.info("Chat completion successful",
                   completion_id=completion_id,
                   total_time=total_time,
                   tokens_per_second=result.get("tokens_per_second", 0))
        
        return response
        
    except Exception as e:
        logger.error("Chat completion failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    if not settings.monitoring_config.enable_metrics:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    return get_metrics()

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", 
                path=request.url.path,
                method=request.method,
                error=str(exc))
    
    return ErrorResponse(
        error="Internal server error",
        detail=str(exc),
        timestamp=datetime.utcnow().isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=settings.log_level.lower())