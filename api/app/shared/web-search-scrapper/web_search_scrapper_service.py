from __future__ import annotations

from typing import Any, Literal

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import get_request_access_token
from app.handlers.request_context.context import request_context


class WebSearchScrapperService:
    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.WEB_SEARCH_SCRAPPER_BASE_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.WEB_SEARCH_SCRAPPER_TIMEOUT_SECONDS

    def _resolve_access_token(self, token: str | None = None) -> str:
        if token:
            return token

        request_token = get_request_access_token()
        if request_token:
            return request_token

        current_request = request_context.get()
        state_token = getattr(getattr(current_request, "state", None), "auth_token", None)
        if isinstance(state_token, str) and state_token:
            return state_token

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Keycloak access token in request context",
        )

    async def _request(
        self,
        *,
        method: str,
        path: str,
        token: str | None = None,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        access_token = self._resolve_access_token(token)
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.base_url}{path}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_body,
                    headers=headers,
                )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Web search scrapper connection error: {exc}",
            ) from exc

        if response.status_code >= 400:
            detail: Any
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise HTTPException(status_code=response.status_code, detail=detail)

        try:
            payload = response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Web search scrapper returned a non-JSON response",
            ) from exc

        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Web search scrapper response must be a JSON object",
            )
        return payload

    async def meta_search(
        self,
        *,
        query: str,
        provider: Literal["searxng", "whoogle"] = "searxng",
        limit: int = 5,
        enrichment: str = "",
        rank: bool = True,
        p_rank_major: float = 0.75,
        extract_url: bool = True,
        markdown: bool = True,
        token: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "query": query,
            "provider": provider,
            "limit": limit,
            "enrichment": enrichment,
            "rank": rank,
            "p_rank_major": p_rank_major,
            "extract_url": extract_url,
            "markdown": markdown,
        }
        return await self._request(
            method="GET",
            path="/api/v1/meta-search/",
            params=params,
            token=token,
        )

    async def url_extract(
        self,
        *,
        url: str,
        markdown: bool = False,
        token: str | None = None,
    ) -> dict[str, Any]:
        params = {"url": url, "markdown": markdown}
        return await self._request(
            method="GET",
            path="/api/v1/url-extract/",
            params=params,
            token=token,
        )

    async def url_extract_batch(
        self,
        *,
        urls: list[str],
        markdown: bool = False,
        token: str | None = None,
    ) -> dict[str, Any]:
        body = {"urls": urls, "markdown": markdown}
        return await self._request(
            method="POST",
            path="/api/v1/url-extract/batch",
            json_body=body,
            token=token,
        )


web_search_scrapper_service = WebSearchScrapperService()
