from typing import Any, NoReturn

import httpx

from app.core.security import get_request_access_token
from app.shared.herandro_services_api.herandro_services_api_models import (
    HsaChatCompletionsRequestModel,
    HsaChatCompletionsResponseModel,
    HsaDataCopilotRequestModel,
    HsaDataCopilotResponseModel,
    HsaResponsesRequestModel,
    HsaResponsesResponseModel,
)


class HerandroServicesApiClient:
    """Cliente HTTP para consumir Herandro Services API desde el servidor."""

    def __init__(self, base_url: str, timeout: float = 900.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _new_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    async def close(self) -> None:
        return None

    def _auth_headers(self) -> dict[str, str]:
        token = get_request_access_token()
        if token is None:
            raise RuntimeError(
                "HSA_REQUEST_TOKEN_NOT_AVAILABLE: authenticate request with "
                "get_current_user (Keycloak) before calling HSA client"
            )
        return {"Authorization": f"Bearer {token}"}

    def _raise_http_error(self, error: httpx.HTTPStatusError, fallback_code: str) -> NoReturn:
        message = fallback_code
        data: Any

        try:
            data = error.response.json()
            if isinstance(data, dict):
                for field in ("detail", "message"):
                    value = data.get(field)
                    if isinstance(value, str) and value.strip():
                        message = value
                        break
        except ValueError:
            pass

        raise RuntimeError(message) from error

    async def data_copilot(
        self,
        request: HsaDataCopilotRequestModel,
    ) -> HsaDataCopilotResponseModel:
        try:
            async with self._new_client() as client:
                response = await client.post(
                    "/ai/v3/data/copilot",
                    json=request.model_dump(),
                    headers=self._auth_headers(),
                )
            response.raise_for_status()
            return HsaDataCopilotResponseModel.model_validate(response.json())
        except httpx.HTTPStatusError as error:
            self._raise_http_error(error, "HSA_DATA_COPILOT_FAILED")

    async def chat_completions(
        self,
        request: HsaChatCompletionsRequestModel,
    ) -> HsaChatCompletionsResponseModel | None:
        try:
            async with self._new_client() as client:
                response = await client.post(
                    "/agent/v1/chat/completions",
                    json=request.model_dump(),
                    headers=self._auth_headers(),
                )
            response.raise_for_status()
            return HsaChatCompletionsResponseModel.model_validate(response.json())
        except httpx.HTTPStatusError as error:
            self._raise_http_error(error, "HSA_CHAT_COMPLETIONS_FAILED")

    async def responses(
        self,
        request: HsaResponsesRequestModel,
    ) -> HsaResponsesResponseModel:
        try:
            payload = request.model_dump(exclude_none=True)
            async with self._new_client() as client:
                response = await client.post(
                    "/ai/v3/responses",
                    json=payload,
                    headers=self._auth_headers(),
                )
            response.raise_for_status()
            return HsaResponsesResponseModel.model_validate(response.json())
        except httpx.HTTPStatusError as error:
            self._raise_http_error(error, "HSA_RESPONSES_FAILED")


_hsa_client_instance: HerandroServicesApiClient | None = None


async def init_hsa_client(base_url: str, timeout: float = 900.0) -> None:
    global _hsa_client_instance
    if _hsa_client_instance is None:
        _hsa_client_instance = HerandroServicesApiClient(base_url=base_url, timeout=timeout)


async def close_hsa_client() -> None:
    global _hsa_client_instance
    if _hsa_client_instance is not None:
        await _hsa_client_instance.close()
        _hsa_client_instance = None


def get_hsa_client() -> HerandroServicesApiClient:
    if _hsa_client_instance is None:
        raise RuntimeError("Herandro Services API client is not initialized")
    return _hsa_client_instance
