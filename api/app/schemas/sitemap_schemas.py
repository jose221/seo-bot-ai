"""
Schemas para el analizador de sitemaps.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class SitemapAnalyzeRequest(BaseModel):
    """Petición para analizar un sitemap index."""
    sitemap_url: str = Field(
        ...,
        description="URL del sitemap index (ej. https://www.pricetravel.com/sitemap-index.xml)",
    )
    min_cluster_size: int = Field(
        10, ge=1, le=1000,
        description="Mínimo de URLs para considerar un patrón significativo",
    )
    max_depth: int = Field(
        4, ge=1, le=10,
        description="Profundidad máxima del árbol de patrones",
    )

    @field_validator("sitemap_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("La URL debe comenzar con http:// o https://")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "sitemap_url": "https://www.pricetravel.com/sitemap-index.xml",
                "min_cluster_size": 10,
                "max_depth": 4,
            }
        }


class SitemapPatternItem(BaseModel):
    """
    Nodo del árbol de patrones SEO (recursivo).
    /hoteles/* → /hoteles/hoteles-en/* → /hoteles/hoteles-en/cancun/*
    """
    pattern: str = Field(..., description="Patrón de path (ej. /hoteles/*)")
    count: int = Field(..., description="Total de URLs que caen bajo este patrón")
    sample_urls: List[str] = Field(
        default_factory=list,
        description="Hasta 5 URLs de ejemplo dentro de este patrón",
    )
    children: Optional[List[SitemapPatternItem]] = Field(
        None,
        description="Sub-patrones hijos, si existen y superan min_cluster_size",
    )


SitemapPatternItem.model_rebuild()


class SitemapAnalyzeResponse(BaseModel):
    """Respuesta del análisis de sitemap con árbol recursivo y filtros disponibles."""
    sitemap_url: str = Field(..., description="URL del sitemap analizado")
    analyzed_at: str = Field(..., description="Fecha/hora del último análisis (ISO 8601 UTC)")
    cache_hit: bool = Field(..., description="True si se devolvió desde caché sin re-analizar")
    total_urls: int = Field(..., description="Total de URLs extraídas del sitemap")
    total_root_patterns: int = Field(..., description="Cantidad de patrones raíz")
    filters: List[str] = Field(
        ...,
        description=(
            "Lista plana de todos los patrones disponibles para usar como filtro. "
            "Pasar cualquiera de estos valores como query param ?filter_pattern=..."
        ),
    )
    active_filter: Optional[str] = Field(
        None,
        description="Filtro aplicado en esta respuesta (si se envió filter_pattern)",
    )
    patterns: List[SitemapPatternItem] = Field(
        ...,
        description="Árbol de patrones (puede estar filtrado si se usó filter_pattern)",
    )

