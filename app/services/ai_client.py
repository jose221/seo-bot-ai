"""
Cliente HTTP para API de Inteligencia Artificial de Herandro Services.
Consume el endpoint /v3/agent/ai/chat/completions
"""
import httpx
from typing import Optional, List
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas.ai_schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    MessageRole,
    MCPTool
)


class AIClient:
    """Cliente para interactuar con la API de IA de Herandro"""

    def __init__(self):
        self.base_url = settings.HERANDRO_API_URL
        self.timeout = 120.0  # 2 minutos para análisis largos

    async def chat_completion(
        self,
        request: ChatCompletionRequest,
        token: str
    ) -> ChatCompletionResponse:
        """
        Enviar petición de chat completion a la API externa.

        Args:
            request: Objeto ChatCompletionRequest con mensajes y configuración
            token: Token de autenticación del usuario

        Returns:
            ChatCompletionResponse con la respuesta del modelo
        """
        url = f"{self.base_url}/v3/agent/ai/chat/completions"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=request.model_dump(exclude_none=True)
                )

                # Manejar errores HTTP
                if response.status_code == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token inválido o expirado para acceder a la IA"
                    )
                elif response.status_code == 422:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Error de validación en la API de IA: {response.text}"
                    )
                elif response.status_code >= 500:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Servicio de IA temporalmente no disponible"
                    )

                response.raise_for_status()

                # Parsear respuesta
                data = response.json()
                return ChatCompletionResponse(**data)

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="La API de IA tardó demasiado en responder"
            )
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error al conectar con la API de IA: {str(e)}"
            )

    async def analyze_seo_content(
        self,
        html_content: str,
        url: str,
        lighthouse_data: Optional[dict] = None,
        token: str = None
    ) -> str:
        """
        Analizar contenido HTML y métricas Lighthouse para SEO.

        Args:
            html_content: HTML completo de la página
            url: URL de la página analizada
            lighthouse_data: Datos de Lighthouse (opcional)
            token: Token de autenticación

        Returns:
            Análisis y sugerencias en texto plano
        """
        # Construir contexto del sistema
        system_message = ChatMessage(
            role=MessageRole.SYSTEM,
            content="""Eres un experto en SEO y optimización web.
Tu trabajo es analizar páginas web y proporcionar sugerencias prácticas y accionables.

Debes analizar:
1. Estructura HTML (títulos, meta tags, semántica)
2. Rendimiento y Core Web Vitals
3. Accesibilidad
4. Mejores prácticas SEO
5. Oportunidades de mejora

Proporciona respuestas en formato estructurado con:
- Resumen ejecutivo
- Problemas críticos
- Sugerencias de mejora priorizadas
- Acciones concretas a tomar""",
            isContext=True
        )

        # Construir mensaje del usuario
        user_content = f"Analiza esta página web:\n\nURL: {url}\n\n"

        if lighthouse_data:
            user_content += f"Métricas Lighthouse:\n"
            user_content += f"- Performance: {lighthouse_data.get('performance_score', 'N/A')}\n"
            user_content += f"- SEO: {lighthouse_data.get('seo_score', 'N/A')}\n"
            user_content += f"- Accesibilidad: {lighthouse_data.get('accessibility_score', 'N/A')}\n"
            user_content += f"- LCP: {lighthouse_data.get('lcp', 'N/A')}ms\n"
            user_content += f"- CLS: {lighthouse_data.get('cls', 'N/A')}\n\n"

        # Limitar HTML para no exceder límites de tokens
        html_preview = html_content[:5000] if len(html_content) > 5000 else html_content
        user_content += f"HTML (primeros 5000 caracteres):\n{html_preview}"

        user_message = ChatMessage(
            role=MessageRole.USER,
            content=user_content
        )

        # Crear request
        request = ChatCompletionRequest(
            messages=[system_message, user_message],
            model="deepseek-chat",
            stream=False
        )

        # Enviar y obtener respuesta
        response = await self.chat_completion(request, token)
        return response.get_content()


# Singleton
_ai_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """Obtener instancia del cliente de IA"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client

