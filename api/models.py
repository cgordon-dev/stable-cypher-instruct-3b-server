from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union, Dict, Any
from enum import Enum

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class ChatMessage(BaseModel):
    role: Role
    content: str
    
class ChatCompletionRequest(BaseModel):
    messages: Optional[List[ChatMessage]] = None
    prompt: Optional[str] = None
    max_tokens: Optional[int] = Field(default=512, ge=1, le=4096)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=40, ge=1, le=100)
    repeat_penalty: Optional[float] = Field(default=1.1, ge=0.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    
    @validator('messages', 'prompt')
    def validate_input(cls, v, values):
        messages = values.get('messages') if 'messages' in values else v
        prompt = values.get('prompt') if 'prompt' in values else (v if 'messages' not in values else None)
        
        if not messages and not prompt:
            raise ValueError('Either messages or prompt must be provided')
        if messages and prompt:
            raise ValueError('Cannot provide both messages and prompt')
        return v
    
    def get_prompt_text(self) -> str:
        if self.prompt:
            return self.prompt
        
        if self.messages:
            parts = []
            for msg in self.messages:
                if msg.role == Role.SYSTEM:
                    parts.append(f"System: {msg.content}")
                elif msg.role == Role.USER:
                    parts.append(f"Human: {msg.content}")
                elif msg.role == Role.ASSISTANT:
                    parts.append(f"Assistant: {msg.content}")
            
            parts.append("Assistant:")
            return "\n\n".join(parts)
        
        return ""

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Usage

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"
    llama_server: Dict[str, Any]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str