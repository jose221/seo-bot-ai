"""
Servicio de análisis dinámico de sitemaps.
Extrae URLs de un sitemap index, las agrupa en patrones jerárquicos recursivos
y devuelve un árbol de patrones SEO ordenado por cantidad de URLs.
"""
import re
import asyncio
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional, Tuple

import httpx


# ---------------------------------------------------------------------------
# Helpers de path
# ---------------------------------------------------------------------------

def _path_segments(url: str) -> List[str]:
    """
    Devuelve los segmentos limpios del path de una URL.
    - Elimina sufijos _<número> típicos de slugs con ID.
    - Ignora segmentos que son solo dígitos o UUIDs.
    """
    parsed = urlparse(url)
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    cleaned: List[str] = []
    for part in parts:
        part = re.sub(r'_\d+$', '', part)
        if re.fullmatch(r'[\d\-a-f]{8,}', part):
            continue
        if part:
            cleaned.append(part)
    return cleaned


# ---------------------------------------------------------------------------
# Motor de clustering jerárquico
# ---------------------------------------------------------------------------

class _PatternNode:
    """Nodo del árbol de patrones SEO."""
    __slots__ = ("segment", "urls", "children")

    def __init__(self, segment: str):
        self.segment = segment
        self.urls: List[str] = []
        self.children: Dict[str, "_PatternNode"] = {}

    def insert(self, url: str, remaining_segments: List[str]) -> None:
        self.urls.append(url)
        if remaining_segments:
            head = remaining_segments[0]
            if head not in self.children:
                self.children[head] = _PatternNode(head)
            self.children[head].insert(url, remaining_segments[1:])

    def to_dict(
        self,
        path_so_far: str,
        min_size: int,
        max_depth: int,
        depth: int = 0,
    ) -> Optional[Dict[str, Any]]:
        count = len(self.urls)
        if count < min_size:
            return None

        current_path = f"{path_so_far}/{self.segment}" if self.segment else path_so_far

        children_dicts: List[Dict[str, Any]] = []
        if depth < max_depth:
            for child in sorted(
                self.children.values(), key=lambda n: len(n.urls), reverse=True
            ):
                child_dict = child.to_dict(current_path, min_size, max_depth, depth + 1)
                if child_dict is not None:
                    children_dicts.append(child_dict)

        node: Dict[str, Any] = {
            "pattern": f"{current_path}/*",
            "count": count,
            "sample_urls": self.urls[:5],
        }
        if children_dicts:
            node["children"] = children_dicts
        return node


class _RootNode:
    """Raíz virtual del árbol."""

    def __init__(self) -> None:
        self.children: Dict[str, _PatternNode] = {}

    def insert(self, url: str) -> None:
        segments = _path_segments(url)
        if not segments:
            return
        head = segments[0]
        if head not in self.children:
            self.children[head] = _PatternNode(head)
        self.children[head].insert(url, segments[1:])

    def build_tree(self, min_size: int, max_depth: int) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for node in sorted(
            self.children.values(), key=lambda n: len(n.urls), reverse=True
        ):
            d = node.to_dict("", min_size, max_depth)
            if d is not None:
                result.append(d)
        return result


# ---------------------------------------------------------------------------
# Resultado del análisis (árbol + lastmod snapshot)
# ---------------------------------------------------------------------------

@dataclass
class SitemapAnalysisResult:
    """Resultado completo del análisis, incluyendo snapshot de lastmod para caché."""
    patterns: List[Dict[str, Any]]
    # Dict { child_sitemap_url: lastmod_str_or_None }
    lastmod_snapshot: Dict[str, Optional[str]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Analizador principal
# ---------------------------------------------------------------------------

class SitemapAnalyzer:
    """Analiza sitemaps y descubre patrones SEO jerárquicos de forma recursiva."""

    NAMESPACES = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    TEXT_URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")

    def __init__(
        self,
        min_cluster_size: int = 10,
        max_depth: int = 4,
        request_delay: float = 1.0,
        user_agent: str = "SEOAnalyzerBot/1.1",
    ):
        self.min_cluster_size = min_cluster_size
        self.max_depth = max_depth
        self.request_delay = request_delay
        self.headers = {"User-Agent": user_agent}

    async def _fetch(self, url: str) -> str:
        await asyncio.sleep(self.request_delay)
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.text
        except httpx.HTTPError as exc:
            print(f"[SitemapAnalyzer] Error al descargar {url}: {exc}")
            return ""

    def _extract_child_sitemaps(self, content: str) -> List[Tuple[str, Optional[str]]]:
        """
        Extrae (loc, lastmod) de un sitemapindex.
        lastmod puede ser None si no está presente.
        """
        result: List[Tuple[str, Optional[str]]] = []
        if not content:
            return result
        try:
            root = ET.fromstring(content)
            for sm in root.findall("sm:sitemap", self.NAMESPACES):
                loc_node = sm.find("sm:loc", self.NAMESPACES)
                lastmod_node = sm.find("sm:lastmod", self.NAMESPACES)
                if loc_node is not None and loc_node.text:
                    lastmod = lastmod_node.text.strip() if lastmod_node is not None and lastmod_node.text else None
                    result.append((loc_node.text.strip(), lastmod))
        except ET.ParseError as exc:
            print(f"[SitemapAnalyzer] XML inválido en index: {exc}")
        return result

    def _extract_urls_from_child(self, content: str) -> List[str]:
        if not content:
            return []
        try:
            root = ET.fromstring(content)
            return [
                node.text.strip()
                for node in root.findall("sm:url/sm:loc", self.NAMESPACES)
                if node.text
            ]
        except ET.ParseError:
            return self.TEXT_URL_PATTERN.findall(content)

    async def analyze(self, index_url: str) -> SitemapAnalysisResult:
        """
        Ejecuta el pipeline completo y devuelve SitemapAnalysisResult
        con el árbol de patrones y el snapshot de lastmod.
        """
        print(f"[SitemapAnalyzer] Analizando: {index_url}")

        index_content = await self._fetch(index_url)
        child_entries = self._extract_child_sitemaps(index_content)  # [(url, lastmod), ...]
        print(f"[SitemapAnalyzer] Sitemaps hijos: {len(child_entries)}")

        lastmod_snapshot: Dict[str, Optional[str]] = {
            url: lastmod for url, lastmod in child_entries
        }

        semaphore = asyncio.Semaphore(5)
        all_urls: List[str] = []

        async def _fetch_child(url: str) -> List[str]:
            async with semaphore:
                content = await self._fetch(url)
                return self._extract_urls_from_child(content)

        results = await asyncio.gather(
            *[_fetch_child(url) for url, _ in child_entries],
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, list):
                all_urls.extend(r)

        print(f"[SitemapAnalyzer] Total URLs: {len(all_urls)}")

        root = _RootNode()
        for url in all_urls:
            root.insert(url)

        patterns = root.build_tree(self.min_cluster_size, self.max_depth)
        return SitemapAnalysisResult(patterns=patterns, lastmod_snapshot=lastmod_snapshot)


# Singleton reutilizable
_analyzer_instance: Optional[SitemapAnalyzer] = None


def get_sitemap_analyzer() -> SitemapAnalyzer:
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = SitemapAnalyzer()
    return _analyzer_instance

