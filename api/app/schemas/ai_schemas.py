"""
Schemas para integración con API de IA de Herandro.
Acepta el contrato real de /agent/v1/chat/completions tanto para request
como para response, incluyendo variantes stream y non-stream.
"""
from enum import Enum
from typing import Any, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Roles de mensajes en chat"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Mensaje individual en el chat"""
    role: MessageRole
    content: Union[str, List[dict[str, Any]]]
    isContext: bool = Field(default=False, description="Si es mensaje de contexto del sistema")


class MCPTool(BaseModel):
    """Configuración de herramientas MCP (Model Context Protocol)"""
    server_name: str
    transport: Optional[str] = None
    command: str
    args: List[str]


class ResponseFormat(BaseModel):
    """Formato de salida solicitado al servicio"""
    type: Literal["json_object", "text"]


class ChatCompletionRequest(BaseModel):
    """Request para la API de Chat Completions"""
    messages: List[ChatMessage]
    session_id: Optional[str] = None
    length_history: Optional[int] = None
    auto_save: Optional[bool] = None
    collection_name: Optional[Union[str, List[str]]] = None
    model: str = Field(
        default="deepseek-v4-flash",
        description="Modelo a usar: deepseek-v4-flash, lowest, etc."
    )
    provider: Optional[str] = None
    mode_debug: Optional[bool] = None
    stream: bool = Field(default=False, description="Si hacer streaming de respuesta")
    mcp_tools: Optional[Union[List[MCPTool], List[dict]]] = Field(
        default=None,
        description="Herramientas MCP a habilitar (ej. playwright)"
    )
    tools: Optional[List[str]] = Field(
        default=None,
        description="Herramientas adicionales a habilitar (ej. playwright)"
    )
    response_format: Optional[ResponseFormat] = None

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
                "model": "deepseek-v4-flash",
                "stream": False,
                "tools":[ "web_search","url_validator", "action_plan"]
            }
        }


class ChatCompletionChoiceMessage(BaseModel):
    """Mensaje de salida en choices para respuestas stream y non-stream"""
    role: Optional[str] = None
    content: Optional[Union[str, List[Any]]] = None
    refusal: Optional[str] = None


class ChatCompletionChoice(BaseModel):
    """Una opción de respuesta del modelo"""
    message: Optional[ChatCompletionChoiceMessage] = None
    delta: Optional[ChatCompletionChoiceMessage] = None
    finish_reason: Optional[str] = None
    index: int = 0


class ChatCompletionUsage(BaseModel):
    """Métricas de uso de tokens"""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ChatCompletionResponse(BaseModel):
    """Respuesta de la API de Chat Completions.
    Soporta el formato nuevo (content top-level) y el formato legacy (choices[]).
    """
    id: Optional[str] = None
    object: str = "chat.completion"
    created: Optional[int] = None
    model: str
    # Formato legacy OpenAI-style
    choices: Optional[List[ChatCompletionChoice]] = None
    # Formato nuevo: content directo en la respuesta
    content: Optional[str] = None
    generated_at: Optional[str] = None
    usage: Optional[ChatCompletionUsage] = None

    def get_content(self) -> str:
        """Obtiene el contenido desde content top-level, message o delta."""
        if self.content:
            return self.content
        if self.choices and len(self.choices) > 0:
            first_choice = self.choices[0]
            if first_choice.message and isinstance(first_choice.message.content, str):
                return first_choice.message.content
            if first_choice.delta and isinstance(first_choice.delta.content, str):
                return first_choice.delta.content
        return ""
