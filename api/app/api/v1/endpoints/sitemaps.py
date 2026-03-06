"""
Endpoint para análisis de sitemaps.

Flujo:
1. Descarga solo el sitemap index (liviano) para obtener el snapshot de lastmod.
2. Compara con la caché en disco (storage/sitemaps/<hash>.json).
3a. Caché vigente  → devuelve el JSON guardado (sin re-analizar sitemaps hijos).
3b. Sin caché o lastmod cambió → analiza completo y sobreescribe la caché.
4. Aplica filtro opcional por prefijo de patrón antes de responder.
"""
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.sitemap_schemas import (
    SitemapAnalyzeRequest,
    SitemapAnalyzeResponse,
    SitemapPatternItem,
)
from app.services.sitemap_analyzer import SitemapAnalyzer
from app.services.sitemap_cache import SitemapCacheService

router = APIRouter()
_cache_service = SitemapCacheService()

# ---------------------------------------------------------------------------
# Helper: descarga ligera del index para obtener snapshot de lastmod
# ---------------------------------------------------------------------------

_NAMESPACES = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


async def _fetch_lastmod_snapshot(sitemap_url: str) -> dict:
    """Descarga solo el sitemap index y extrae {child_url: lastmod}."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                sitemap_url,
                headers={"User-Agent": "SEOAnalyzerBot/1.1"},
            )
            resp.raise_for_status()
            content = resp.text
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo descargar el sitemap index: {exc}",
        )

    snapshot: dict = {}
    try:
        root = ET.fromstring(content)
        for sm in root.findall("sm:sitemap", _NAMESPACES):
            loc = sm.find("sm:loc", _NAMESPACES)
            lastmod = sm.find("sm:lastmod", _NAMESPACES)
            if loc is not None and loc.text:
                snapshot[loc.text.strip()] = (
                    lastmod.text.strip()
                    if lastmod is not None and lastmod.text
                    else None
                )
    except ET.ParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El sitemap index no es XML válido: {exc}",
        )

    return snapshot


# ---------------------------------------------------------------------------
# Conversión dict → schema recursivo
# ---------------------------------------------------------------------------

def _build_item(raw: dict) -> SitemapPatternItem:
    return SitemapPatternItem(
        pattern=raw["pattern"],
        count=raw["count"],
        sample_urls=raw.get("sample_urls", []),
        children=(
            [_build_item(c) for c in raw["children"]]
            if raw.get("children")
            else None
        ),
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/sitemaps/analyze",
    response_model=SitemapAnalyzeResponse,
    summary="Analizar sitemap index (caché + filtros)",
    description=(
        "Analiza un sitemap index y devuelve un árbol jerárquico recursivo de patrones SEO. "
        "El resultado se guarda en disco. En solicitudes posteriores se comparan los lastmod "
        "del index: si no cambiaron se devuelve la caché sin re-analizar. "
        "Usa **filter_pattern** (query param) para filtrar el árbol por prefijo de patrón, "
        "ej. `?filter_pattern=/es/hoteles/*`"
    ),
    tags=["Sitemaps"],
)
async def analyze_sitemap(
    body: SitemapAnalyzeRequest,
    filter_pattern: Optional[str] = Query(
        None,
        description=(
            "Filtra el árbol de patrones por prefijo. "
            "Usa cualquier valor de la lista 'filters' de la respuesta."
        ),
    ),
    current_user: User = Depends(get_current_user),
) -> SitemapAnalyzeResponse:

    # 1. Obtener snapshot actual de lastmod (solo descarga el index)
    current_snapshot = await _fetch_lastmod_snapshot(body.sitemap_url)

    # 2. Decidir si necesitamos re-analizar
    needs_reanalysis = _cache_service.needs_reanalysis(body.sitemap_url, current_snapshot)

    if needs_reanalysis:
        # 3a. Análisis completo
        analyzer = SitemapAnalyzer(
            min_cluster_size=body.min_cluster_size,
            max_depth=body.max_depth,
        )
        try:
            result = await analyzer.analyze(body.sitemap_url)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error durante el análisis del sitemap: {exc}",
            )

        if not result.patterns:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron URLs en el sitemap proporcionado.",
            )

        total_urls = sum(p["count"] for p in result.patterns)
        data = _cache_service.save(
            sitemap_url=body.sitemap_url,
            patterns=result.patterns,
            lastmod_snapshot=result.lastmod_snapshot,
            total_urls=total_urls,
        )
        cache_hit = False
    else:
        # 3b. Usar caché
        data = _cache_service.load(body.sitemap_url)
        if data is None:
            # Por si acaso se borró el archivo entre la validación y la lectura
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Inconsistencia en caché. Reintenta la solicitud.",
            )
        cache_hit = True

    # 4. Aplicar filtro (siempre sobre los datos completos)
    data = _cache_service.apply_filter(data, filter_pattern)

    # 5. Construir respuesta tipada
    return SitemapAnalyzeResponse(
        sitemap_url=data["sitemap_url"],
        analyzed_at=data["analyzed_at"],
        cache_hit=cache_hit,
        total_urls=data["total_urls"],
        total_root_patterns=data["total_root_patterns"],
        filters=data.get("filters", []),
        active_filter=data.get("active_filter"),
        patterns=[_build_item(p) for p in data["patterns"]],
    )
