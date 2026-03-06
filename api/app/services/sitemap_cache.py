"""
Servicio de caché en disco para análisis de sitemaps.

Flujo:
1. Al recibir una petición, se descarga solo el sitemap index (liviano).
2. Se compara el snapshot de lastmod con el guardado en caché.
3. Si son iguales → se devuelve el JSON en caché (sin re-analizar).
4. Si hay diferencias → se re-analiza completo y se sobreescribe la caché.

Formato del archivo JSON en storage/sitemaps/<hash>.json:
{
  "sitemap_url": "https://...",
  "analyzed_at": "2026-03-05T10:00:00",
  "lastmod_snapshot": { "https://child.xml": "2025-02-12", ... },
  "total_urls": 45320,
  "total_root_patterns": 8,
  "filters": ["/*", "/es/*", "/es/hoteles/*", ...],
  "patterns": [ { "pattern": ..., "count": ..., ... }, ... ]
}
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Directorio base de caché — relativo al package, resuelto en runtime
_STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage" / "sitemaps"


def _cache_path(sitemap_url: str) -> Path:
    """Devuelve la ruta del archivo JSON de caché para la URL dada."""
    slug = hashlib.sha256(sitemap_url.encode()).hexdigest()[:16]
    _STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    return _STORAGE_DIR / f"{slug}.json"


def _read_cache(sitemap_url: str) -> Optional[Dict[str, Any]]:
    """Lee el JSON de caché si existe; devuelve None si no existe o está corrupto."""
    path = _cache_path(sitemap_url)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(sitemap_url: str, data: Dict[str, Any]) -> None:
    """Escribe (o sobreescribe) el JSON de caché para la URL dada."""
    path = _cache_path(sitemap_url)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _snapshots_equal(
    cached_snapshot: Dict[str, Optional[str]],
    current_snapshot: Dict[str, Optional[str]],
) -> bool:
    """
    Compara los snapshots de lastmod.
    Son iguales si:
    - Contienen exactamente los mismos sitemaps hijos.
    - Todos los lastmod coinciden (o ambos son None).
    """
    if set(cached_snapshot.keys()) != set(current_snapshot.keys()):
        return False
    return all(cached_snapshot.get(k) == current_snapshot.get(k) for k in current_snapshot)


# ---------------------------------------------------------------------------
# Extracción plana de patrones para filtros
# ---------------------------------------------------------------------------

def _collect_all_patterns(patterns: List[Dict[str, Any]]) -> List[str]:
    """
    Recorre el árbol recursivamente y devuelve una lista plana con todos los
    valores de 'pattern' encontrados, ordenados alfabéticamente.
    """
    result: List[str] = []

    def _walk(nodes: List[Dict[str, Any]]) -> None:
        for node in nodes:
            result.append(node["pattern"])
            if node.get("children"):
                _walk(node["children"])

    _walk(patterns)
    return sorted(set(result))


# ---------------------------------------------------------------------------
# Filtrado del árbol
# ---------------------------------------------------------------------------

def _filter_tree(
    patterns: List[Dict[str, Any]],
    filter_pattern: str,
) -> List[Dict[str, Any]]:
    """
    Devuelve solo los nodos cuyo 'pattern' empieza con filter_pattern
    (búsqueda de prefijo), preservando la jerarquía.

    Ejemplo: filter_pattern="/es/hoteles" mostraría:
      /es/hoteles/*  →  /es/hoteles/hoteles-en/*  → ...
    """
    result: List[Dict[str, Any]] = []

    def _walk(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        matched: List[Dict[str, Any]] = []
        for node in nodes:
            # Este nodo coincide directamente
            if node["pattern"].startswith(filter_pattern):
                matched.append(node)
            # Puede que un hijo coincida aunque el padre no
            elif node.get("children"):
                sub = _walk(node["children"])
                if sub:
                    # Incluir el padre como contexto pero sólo con los hijos filtrados
                    shallow = {k: v for k, v in node.items() if k != "children"}
                    shallow["children"] = sub
                    matched.append(shallow)
        return matched

    return _walk(patterns)


# ---------------------------------------------------------------------------
# API pública del servicio de caché
# ---------------------------------------------------------------------------

class SitemapCacheService:
    """
    Gestiona la lectura, validación y escritura de la caché en disco.
    Principio de responsabilidad única: solo sabe de caché, no de análisis.
    """

    def needs_reanalysis(
        self,
        sitemap_url: str,
        current_snapshot: Dict[str, Optional[str]],
    ) -> bool:
        """
        Devuelve True si se debe re-analizar (sin caché o lastmod cambió).
        """
        cached = _read_cache(sitemap_url)
        if cached is None:
            print(f"[SitemapCache] Sin caché para {sitemap_url} → re-análisis")
            return True

        cached_snapshot = cached.get("lastmod_snapshot", {})
        if not _snapshots_equal(cached_snapshot, current_snapshot):
            print(f"[SitemapCache] lastmod cambió para {sitemap_url} → re-análisis")
            return True

        print(f"[SitemapCache] Caché vigente para {sitemap_url}")
        return False

    def save(
        self,
        sitemap_url: str,
        patterns: List[Dict[str, Any]],
        lastmod_snapshot: Dict[str, Optional[str]],
        total_urls: int,
    ) -> Dict[str, Any]:
        """
        Construye el objeto completo de caché, lo persiste en disco y lo devuelve.
        """
        filters = _collect_all_patterns(patterns)
        data: Dict[str, Any] = {
            "sitemap_url": sitemap_url,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "lastmod_snapshot": lastmod_snapshot,
            "total_urls": total_urls,
            "total_root_patterns": len(patterns),
            "filters": filters,
            "patterns": patterns,
        }
        _write_cache(sitemap_url, data)
        print(f"[SitemapCache] Guardado en disco: {_cache_path(sitemap_url)}")
        return data

    def load(self, sitemap_url: str) -> Optional[Dict[str, Any]]:
        """Carga la caché sin validar. Devuelve None si no existe."""
        return _read_cache(sitemap_url)

    def apply_filter(
        self,
        data: Dict[str, Any],
        filter_pattern: Optional[str],
    ) -> Dict[str, Any]:
        """
        Aplica un filtro de prefijo sobre los patrones y devuelve una copia
        del objeto de caché con los patrones filtrados (filters permanece completo).
        """
        if not filter_pattern:
            return data

        filtered_patterns = _filter_tree(data["patterns"], filter_pattern)
        return {
            **data,
            "patterns": filtered_patterns,
            "total_root_patterns": len(filtered_patterns),
            # filters siempre muestra el listado completo disponible
            "filters": data.get("filters", []),
            "active_filter": filter_pattern,
        }

