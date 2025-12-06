"""
Cliente HTTP para API de Inteligencia Artificial de Herandro Services.
Consume el endpoint /v3/agent/ai/chat/completions
"""
import httpx
from typing import Optional
from fastapi import HTTPException, status
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

from app.helpers import extract_domain
from app.schemas.ai_schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    MessageRole
)
from app.core.config import settings
from app.services.seo_analyzer import SEOAnalyzer


class AIClient:
    """Cliente para interactuar con la API de IA de Herandro"""

    def __init__(self):
        self.base_url = settings.HERANDRO_API_URL
        self.timeout = None  # 2 minutos para análisis largos

        # Configurar Jinja2 para cargar plantillas de prompts
        prompts_dir = Path(__file__).parent.parent / "prompts"
        self.jinja_env = Environment(
            loader=FileSystemLoader(prompts_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True
        )

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
                    print(request.model_dump(exclude_none=True))
                    f_response = response.json()
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Servicio de IA temporalmente no disponible"
                    )

                response.raise_for_status()

                # Parsear respuesta
                data = response.json()
                obj_response = data[0]
                return ChatCompletionResponse(**obj_response)

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
        # Construir contexto del sistema usando plantilla Jinja
        seo_analyzer = SEOAnalyzer(url=extract_domain(url), html_content=html_content)

        # Renderizar prompt del sistema desde plantilla
        system_template = self.jinja_env.get_template("seo_analysis.jinja")
        system_content = system_template.render(
            robots_analysis=seo_analyzer.analyze_robots_txt(),
            structured_data=seo_analyzer.analyze_structured_data()
        )

        system_message = ChatMessage(
            role=MessageRole.SYSTEM,
            content=system_content,
            isContext=True
        )

        # Renderizar prompt del usuario desde plantilla
        html_preview = html_content

        user_template = self.jinja_env.get_template("user_analysis.jinja")
        user_content = user_template.render(
            url=url,
            lighthouse_data=lighthouse_data,
            html_content=html_preview
        )

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

    async def analyze_audit_comparison(
        self,
        comparison_data: dict,
        token: str
    ) -> str:
        """
        Analizar comparación de auditorías usando IA.

        Args:
            comparison_data: Datos de comparación estructurados
            token: Token de autenticación

        Returns:
            Análisis textual de la comparación
        """
        # Renderizar prompt desde plantilla
        template = self.jinja_env.get_template("audit_comparison.jinja")
        prompt_content = template.render(**comparison_data)

        user_message = ChatMessage(
            role=MessageRole.USER,
            content=prompt_content
        )

        request = ChatCompletionRequest(
            messages=[user_message],
            model="deepseek-chat",
            stream=False,
            tools=["web_search"],
            mcp_tools=[
                {
                    "server_name": "playwright-browser",
                    "transport": "stdio",  # Local process
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-playwright"
                    ],
                    "env": {
                        # Opcional: Define si quieres ver el navegador (headless=False) o no
                        # Por defecto suele ser headless en servidores
                        "PLAYWRIGHT_HEADLESS": "true"
                    }
                },
                {
                    "server_name": "lighthouse-audit",
                    "transport": "stdio",
                    "command": "npx",
                    "args": [
                        "-y",
                        "lighthouse-mcp"
                    ],
                    "env": {
                        # Opcional: Chrome flags si estás en un entorno Docker sin cabeza
                        # "CHROME_FLAGS": "--no-sandbox --headless"
                    }
                }
            ]
        )

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

