import httpx
import json
import logging
from typing import Optional
from fastapi import HTTPException, status
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import tiktoken

from app.helpers import extract_domain
from app.schemas.ai_schemas import (
  ChatCompletionRequest,
  ChatCompletionResponse,
  ChatMessage,
  MessageRole
)
from app.core.config import settings
from app.services.seo_analyzer import SEOAnalyzer

logger = logging.getLogger(__name__)

class AIClient:
  def __init__(self):
    self.base_url = settings.HERANDRO_API_URL
    self.timeout = httpx.Timeout(900.0, read=900.0)

    prompts_dir = Path(__file__).parent.parent / "prompts"
    self.jinja_env = Environment(
      loader=FileSystemLoader(prompts_dir),
      autoescape=select_autoescape(),
      trim_blocks=True,
      lstrip_blocks=True
    )

  def count_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
    try:
      encoding = tiktoken.encoding_for_model(model)
    except KeyError:
      encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))

  async def chat_completion(
    self,
    request: ChatCompletionRequest,
    token: str
  ) -> ChatCompletionResponse:
    url = f"{self.base_url}/agent/v1/chat/completions"

    # Se fuerza la cabecera para mantener la conexion viva a nivel TCP
    headers = {
      "Authorization": f"Bearer {token}",
      "Content-Type": "application/json",
      "Connection": "keep-alive"
    }

    payload = request.model_dump(exclude_none=True)
    logger.info(f"Initiating AI chat completion request to {url}")
    logger.info(f"Request payload keys: {list(payload.keys())}")
    logger.info(f"Request headers: {headers}")

    try:
      # Desactivamos el pool de conexiones y forzamos HTTP/1.1
      # para evitar que el socket se cierre por inactividad estricta de HTTP/2
      limits = httpx.Limits(max_keepalive_connections=0)

      async with httpx.AsyncClient(timeout=self.timeout, limits=limits, http2=False) as client:
        response = await client.post(
          url,
          headers=headers,
          json=payload
        )

        logger.info(f"Received response with status code: {response.status_code}")

        if response.status_code == 401:
          logger.warning("Authentication failed: Invalid or expired token")
          raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado para acceder a la IA"
          )
        elif response.status_code == 422:
          logger.error(f"Validation error from AI API: {response.text}")
          raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error de validacion en la API de IA: {response.text}"
          )
        elif response.status_code >= 500:
          logger.error(f"Server error from AI API: {response.text}")
          raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de IA temporalmente no disponible"
          )

        response.raise_for_status()

        data = None
        for line in response.text.split('\n'):
          if line.startswith('data: '):
            json_str = line[6:]
            try:
              data = json.loads(json_str)
              break
            except json.JSONDecodeError as e:
              logger.error(f"Failed to parse SSE JSON data: {e} - Line: {json_str}")
              continue

        if data is None:
          try:
            data = response.json()
          except ValueError:
            logger.error(f"Failed to parse standard JSON response: {response.text}")
            raise

        if isinstance(data, list):
          obj_response = data[0]
        elif isinstance(data, dict):
          obj_response = data
        else:
          logger.error(f"Unexpected data format: {type(data).__name__}")
          raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Formato de respuesta IA inesperado: {type(data).__name__}"
          )

        logger.info("Successfully parsed AI response")
        return ChatCompletionResponse.model_validate(obj_response)

    except httpx.TimeoutException as e:
      logger.exception("Timeout occurred while waiting for AI API response")
      raise HTTPException(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        detail="La API de IA tardo demasiado en responder"
      )
    except httpx.RequestError as e:
      logger.exception(f"Network request error occurred: {str(e)}")
      raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Error de red al conectar con la API de IA: {str(e)}"
      )
    except Exception as e:
      logger.exception(f"An unexpected error occurred: {str(e)}")
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error interno al procesar la respuesta de la IA"
      )

  async def analyze_seo_content(
    self,
    html_content: str,
    url: str,
    lighthouse_data: Optional[dict] = None,
    token: str = None,
    documentation_context: Optional[str] = None
  ) -> dict:
    seo_analyzer = SEOAnalyzer(url=extract_domain(url), html_content=html_content)

    system_template = self.jinja_env.get_template("seo_analysis.jinja")
    system_content = system_template.render(
      robots_analysis=seo_analyzer.analyze_robots_txt(),
      structured_data=seo_analyzer.analyze_structured_data(),
      documentation_context=documentation_context
    )

    system_message = ChatMessage(
      role=MessageRole.SYSTEM,
      content=system_content,
      isContext=True
    )

    html_preview = html_content

    user_template = self.jinja_env.get_template("user_analysis.jinja")
    user_content = user_template.render(
      url=url,
      lighthouse_data=lighthouse_data,
      html_content=html_preview,
      documentation_context=documentation_context
    )

    user_message = ChatMessage(
      role=MessageRole.USER,
      content=user_content
    )

    request = ChatCompletionRequest(
      messages=[system_message, user_message],
      model="deepseek-v4-flash",
      stream=False
    )

    input_text = f"{system_content}\n{user_content}"
    input_tokens = self.count_tokens(input_text)

    response = await self.chat_completion(request, token)
    content = response.get_content()

    if response.usage and response.usage.total_tokens:
      usage = {
        "prompt_tokens": response.usage.prompt_tokens or input_tokens,
        "completion_tokens": response.usage.completion_tokens or self.count_tokens(content),
        "total_tokens": response.usage.total_tokens,
      }
    else:
      output_tokens = self.count_tokens(content)
      usage = {
        "prompt_tokens": input_tokens,
        "completion_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
      }

    return {
      "content": content,
      "usage": usage
    }

  async def analyze_audit_comparison(
    self,
    comparison_data: dict,
    token: str
  ) -> dict:
    template = self.jinja_env.get_template("audit_comparison.jinja")
    prompt_content = template.render(**comparison_data)

    user_message = ChatMessage(
      role=MessageRole.USER,
      content=prompt_content
    )

    request = ChatCompletionRequest(
      messages=[user_message],
      model="deepseek-v4-flash",
      stream=False,
      mcp_tools=[
        {
          "server_name": "playwright-browser",
          "transport": "stdio",
          "command": "npx",
          "args": [
            "-y",
            "@modelcontextprotocol/server-playwright"
          ]
        }
      ]
    )

    input_tokens = self.count_tokens(prompt_content)

    response = await self.chat_completion(request, token)
    content = response.get_content()

    if response.usage and response.usage.total_tokens:
      usage = {
        "prompt_tokens": response.usage.prompt_tokens or input_tokens,
        "completion_tokens": response.usage.completion_tokens or self.count_tokens(content),
        "total_tokens": response.usage.total_tokens,
      }
    else:
      output_tokens = self.count_tokens(content)
      usage = {
        "prompt_tokens": input_tokens,
        "completion_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
      }

    return {
      "content": content,
      "usage": usage
    }


_ai_client: Optional[AIClient] = None

def get_ai_client() -> AIClient:
  global _ai_client
  if _ai_client is None:
    _ai_client = AIClient()
  return _ai_client
