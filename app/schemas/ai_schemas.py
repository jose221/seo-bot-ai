"""
Schemas para integración con API de IA de Herandro.
Mapea exactamente la estructura de /v3/agent/ai/chat/completions
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class MessageRole(str, Enum):
    """Roles de mensajes en chat"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Mensaje individual en el chat"""
    role: MessageRole
    content: str
    isContext: bool = Field(default=False, description="Si es mensaje de contexto del sistema")


class MCPTool(BaseModel):
    """Configuración de herramientas MCP (Model Context Protocol)"""
    server_name: str
    command: str
    args: List[str]


class ChatCompletionRequest(BaseModel):
    """Request para la API de Chat Completions"""
    messages: List[ChatMessage]
    model: str = Field(
        default="deepseek-chat",
        description="Modelo a usar: deepseek-chat, lowest, etc."
    )
    stream: bool = Field(default=False, description="Si hacer streaming de respuesta")
    mcp_tools: Optional[List[MCPTool]] = Field(
        default=None,
        description="Herramientas MCP a habilitar (ej. playwright)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un experto en SEO y análisis web",
                        "isContext": True
                    },
                    {
                        "role": "user",
                        "content": "Analiza este HTML y dame sugerencias SEO"
                    }
                ],
                "model": "deepseek-chat",
                "stream": False
            }
        }


class ChatCompletionChoice(BaseModel):
    """Una opción de respuesta del modelo"""
    delta: ChatMessage
    finish_reason: Optional[str] = None
    index: int = 0


class ChatCompletionUsage(BaseModel):
    """Métricas de uso de tokens"""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ChatCompletionResponse(BaseModel):
    """Respuesta de la API de Chat Completions"""
    id: Optional[str] = None
    object: str = "chat.completion"
    created: Optional[int] = None
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None

    def get_content(self) -> str:
        """Helper para obtener el contenido de la primera respuesta"""
        if self.choices and len(self.choices) > 0:
            return self.choices[0].delta.content
        return ""

