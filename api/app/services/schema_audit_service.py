"""
Servicio para auditoría de schemas (original vs propuesto vs nuevo).
"""
import json
import re
from typing import Any, Dict, List, Optional, Set

from app.services.ai_client import AIClient
from app.schemas.ai_schemas import ChatMessage, MessageRole, ChatCompletionRequest

# Límites para minificación de esquemas antes de enviar a la IA
_MAX_SCHEMA_ITEMS = 40       # máximo de objetos en una lista raíz de esquemas (sin contar @graph)
_MAX_ARRAY_ITEMS = 15        # máximo de ítems en arrays internos (reviews, mainEntity, containsPlace…)

# Claves cuyos arrays se truncan SIEMPRE (independiente del @type del nodo padre)
_ALWAYS_TRUNCABLE_KEYS = {
    "review", "reviews",
    "performer", "performers",
    "sponsor",
    "event", "events",
    "openingHoursSpecification",
    "amenityFeature",
    "member", "members",
    "publishedOn",
    "contributor",
}

# Claves que se truncan SOLO si el @type del nodo padre NO es uno de los tipos excluidos
# (por ejemplo, itemListElement de BreadcrumbList no debe truncarse)
_CONDITIONAL_TRUNCABLE_KEYS = {
    "itemListElement",   # truncar en ItemList, pero NO en BreadcrumbList
    "mainEntity",        # truncar en FAQPage con muchas preguntas
    "containsPlace",
    "hasPart", "isPartOf",
    "contactPoint", "contactPoints",
    "sameAs",
    "image", "images",
    "hasOfferCatalog",
    "author",
    "about",
    "item",
}

# @types cuyos itemListElement / mainEntity NO se deben truncar (son navegación crítica)
_NO_TRUNCATE_TYPES = {"BreadcrumbList", "SiteNavigationElement"}

# Clave "offers" sólo se trunca si es lista (AggregateOffer.offers puede ser un dict)
_OFFERS_KEY = "offers"


class SchemaAuditService:
    """Lógica de validación y comparación de esquemas."""

    def __init__(self):
        self.ai_client = AIClient()

    def validate_schema_payload(self, payload: Any, label: str) -> Dict[str, Any]:
        """
        Validación estructural básica para JSON-LD / schema.org.
        """
        errors: List[str] = []
        warnings: List[str] = []

        if payload is None:
            return {
                "label": label,
                "is_valid": False,
                "errors": [f"{label}: esquema no proporcionado"],
                "warnings": []
            }

        items = self._normalize_to_items(payload)
        if not items:
            return {
                "label": label,
                "is_valid": False,
                "errors": [f"{label}: el esquema debe ser un objeto o lista de objetos JSON"],
                "warnings": []
            }

        has_schema_context = False
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{label}[{idx}]: cada item debe ser objeto JSON")
                continue

            item_context = item.get("@context")
            if isinstance(item_context, str) and "schema.org" in item_context:
                has_schema_context = True

            is_open_graph = any(
              isinstance(k, str) and "http://ogp.me/ns#" in k
              for k in item.keys()
            )

            item_type = item.get("@type")
            is_graph_root = "@graph" in item
            # Nueva lógica: solo agregar error si no tiene @type y tampoco contiene clave con 'http://www.w3.org/1999'
            if not item_type:
                has_w3c_key = any(
                    isinstance(k, str) and "http://www.w3.org/1999" in k
                    for k in item.keys()
                )
                if not has_w3c_key and not is_open_graph and not is_graph_root:
                    errors.append(f"{label}[{idx}]: falta @type al item: {json.dumps(item, ensure_ascii=False)}")
            elif not isinstance(item_type, (str, list)):
                errors.append(f"{label}[{idx}]: @type debe ser string o lista")

            for key in item.keys():
                if not isinstance(key, str):
                    errors.append(f"{label}[{idx}]: hay una clave no-string")
                elif " " in key:
                    warnings.append(f"{label}[{idx}]: clave con espacio detectada ({key})")

        if not has_schema_context:
            warnings.append(
                f"{label}: no se detectó @context con schema.org (se recomienda usar https://schema.org)"
            )

        return {
            "label": label,
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "items_count": len(items)
        }

    def build_structural_comparison(
        self,
        original_schema: Any,
        proposed_schema: Any,
        incoming_schema: Any
    ) -> Dict[str, Any]:
        original_items = self._normalize_to_items(original_schema)
        proposed_items = self._normalize_to_items(proposed_schema)
        incoming_items = self._normalize_to_items(incoming_schema)

        original_types = self._extract_types(original_items)
        proposed_types = self._extract_types(proposed_items)
        incoming_types = self._extract_types(incoming_items)

        original_integrity = self._check_original_integrity(original_items, incoming_items)
        comparison_table = self._build_schema_comparison_table(proposed_items, incoming_items)

        return {
            "types": {
                "original": sorted(list(original_types)),
                "proposed": sorted(list(proposed_types)),
                "incoming": sorted(list(incoming_types)),
            },
            "delta": {
                "implemented_from_proposed": sorted(list((incoming_types & proposed_types) - original_types)),
                "pending_from_proposed": sorted(list(proposed_types - incoming_types)),
                "new_not_in_proposed": sorted(list(incoming_types - proposed_types)),
                "kept_from_original": sorted(list(original_types & incoming_types)),
            },
            "comparison_table": comparison_table,
            "original_integrity": original_integrity
        }

    def extract_proposed_schema_from_text(self, text: Any) -> Optional[Any]:
        """
        Extrae propuesta de schema en formato JSON/JSON-LD desde texto de propuesta.
        Prioriza bloques ```json.
        """
        if not text:
            return None

        if isinstance(text, dict):
            text = text.get("content") or text.get("analysis") or str(text)

        if not isinstance(text, str):
            text = str(text)

        # 1) Bloques explícitos json
        json_code_blocks = re.findall(r"```json\s*([\s\S]*?)\s*```", text)
        for raw in json_code_blocks:
            parsed = self._safe_json_parse(raw)
            if parsed is not None:
                return parsed

        # 2) Bloques genéricos
        generic_blocks = re.findall(r"```\s*([\s\S]*?)\s*```", text)
        for raw in generic_blocks:
            parsed = self._safe_json_parse(raw)
            if parsed is not None:
                return parsed

        # 3) Intento global (si todo el texto es json)
        parsed = self._safe_json_parse(text)
        if parsed is not None:
            return parsed

        return None

    async def generate_triple_comparison_ai(
        self,
        original_schema: Any,
        proposed_schema: Any,
        incoming_schema: Any,
        structural_result: Dict[str, Any],
        token: str
    ) -> Dict[str, Any]:
        template = self.ai_client.jinja_env.get_template("schema_audit_comparison.jinja")

        prompt_content = template.render(
            original_schema=self._minify_schema_for_ai(original_schema),
            proposed_schema=self._minify_schema_for_ai(proposed_schema),
            incoming_schema=self._minify_schema_for_ai(incoming_schema),
            structural_result=structural_result
        )

        request = ChatCompletionRequest(
            messages=[ChatMessage(role=MessageRole.USER, content=prompt_content)],
            model="deepseek-chat",
            stream=False
        )

        input_tokens = self.ai_client.count_tokens(prompt_content)
        response = await self.ai_client.chat_completion(request, token)
        content = response.get_content()
        output_tokens = self.ai_client.count_tokens(content)

        return {
            "content": content,
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        }

    async def generate_cqrs_solid_model_ai(
        self,
        proposed_schema: Any,
        incoming_schema: Any,
        programming_language: Optional[str],
        token: str
    ) -> Dict[str, Any]:
        template = self.ai_client.jinja_env.get_template("schema_cqrs_solid_model.jinja")

        prompt_content = template.render(
            proposed_schema=self._minify_schema_for_ai(proposed_schema),
            incoming_schema=self._minify_schema_for_ai(incoming_schema),
            programming_language=programming_language or "typescript"
        )

        request = ChatCompletionRequest(
            messages=[ChatMessage(role=MessageRole.USER, content=prompt_content)],
            model="deepseek-chat",
            stream=False
        )

        input_tokens = self.ai_client.count_tokens(prompt_content)
        response = await self.ai_client.chat_completion(request, token)
        content = response.get_content()
        output_tokens = self.ai_client.count_tokens(content)

        return {
            "content": content,
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        }

    def _safe_json_parse(self, raw: str) -> Optional[Any]:
        raw = (raw or "").strip()
        if not raw:
            return None

        if not (raw.startswith("{") or raw.startswith("[")):
            return None

        try:
            return json.loads(raw)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Minificación de esquemas para reducir tokens en prompts de IA
    # ------------------------------------------------------------------

    def _truncate_arrays_in_node(self, node: Any, max_items: int = _MAX_ARRAY_ITEMS) -> Any:
        """
        Recorre recursivamente un nodo y trunca arrays de claves conocidas.
        - Arrays en _ALWAYS_TRUNCABLE_KEYS: siempre se truncan.
        - Arrays en _CONDITIONAL_TRUNCABLE_KEYS: se truncan salvo que el @type
          del nodo actual esté en _NO_TRUNCATE_TYPES (ej. BreadcrumbList).
        - Nodos del @graph raíz: NUNCA se limitan en cantidad.
        """
        if isinstance(node, dict):
            node_type = node.get("@type", "")
            # Normalizar a string si viene como lista (ej. ["Hotel", "LodgingBusiness"])
            if isinstance(node_type, list):
                node_type = node_type[0] if node_type else ""

            is_protected_type = node_type in _NO_TRUNCATE_TYPES

            result: Dict[str, Any] = {}
            for key, value in node.items():
                if not isinstance(value, list):
                    # Recursión normal para dicts anidados
                    result[key] = self._truncate_arrays_in_node(value, max_items)
                    continue

                should_truncate = False
                if key in _ALWAYS_TRUNCABLE_KEYS:
                    should_truncate = True
                elif key == _OFFERS_KEY:
                    # offers sólo se trunca si es una lista (no un dict/objeto único)
                    should_truncate = True
                elif key in _CONDITIONAL_TRUNCABLE_KEYS:
                    # Solo truncar si el nodo padre NO es un tipo protegido
                    should_truncate = not is_protected_type

                if should_truncate and len(value) > max_items:
                    result[key] = [self._truncate_arrays_in_node(v, max_items) for v in value[:max_items]]
                    result[f"_{key}_truncated"] = f"(mostrando {max_items}/{len(value)} ítems)"
                else:
                    result[key] = [self._truncate_arrays_in_node(v, max_items) for v in value]

            return result

        elif isinstance(node, list):
            return [self._truncate_arrays_in_node(item, max_items) for item in node]

        return node

    def _minify_schema_for_ai(
        self,
        schema: Any,
        max_array_items: int = _MAX_ARRAY_ITEMS
    ) -> Any:
        """
        Minifica un schema reduciendo arrays internos dentro de cada nodo.
        Los nodos raíz (incluyendo los del @graph) NO se limitan en cantidad
        para no perder tipos importantes (BreadcrumbList, FAQPage, etc.).
        """
        if schema is None:
            return schema

        # Si viene como string JSON, parsear primero
        parsed = schema
        if isinstance(schema, str):
            try:
                parsed = json.loads(schema)
            except Exception:
                return schema

        # Caso @graph: preservar todos los nodos raíz, solo truncar internamente
        if isinstance(parsed, dict) and "@graph" in parsed and isinstance(parsed["@graph"], list):
            minified_graph = [
                self._truncate_arrays_in_node(node, max_array_items)
                if isinstance(node, dict) else node
                for node in parsed["@graph"]
            ]
            return {**parsed, "@graph": minified_graph}

        # Lista de nodos raíz (sin @graph): preservar todos, truncar internamente
        if isinstance(parsed, list):
            return [
                self._truncate_arrays_in_node(item, max_array_items)
                if isinstance(item, dict) else item
                for item in parsed
            ]

        # Dict único
        if isinstance(parsed, dict):
            return self._truncate_arrays_in_node(parsed, max_array_items)

        return parsed

    def _normalize_to_items(self, payload: Any) -> List[Dict[str, Any]]:
        if payload is None:
            return []

        parsed = payload
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except Exception:
                return []

        if isinstance(parsed, dict):
            # Manejo de @graph
            if "@graph" in parsed and isinstance(parsed["@graph"], list):
                graph_items = [item for item in parsed["@graph"] if isinstance(item, dict)]
                return graph_items if graph_items else [parsed]
            return [parsed]

        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]

        return []

    def _extract_types(self, items: List[Dict[str, Any]]) -> Set[str]:
        types: Set[str] = set()
        for item in items:
            value = item.get("@type")
            if isinstance(value, list):
                for t in value:
                    if isinstance(t, str) and t.strip():
                        types.add(t.strip())
            elif isinstance(value, str) and value.strip():
                types.add(value.strip())
        return types

    def _build_schema_comparison_table(
        self,
        proposed_items: List[Dict[str, Any]],
        incoming_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        proposed_by_type = self._index_by_type(proposed_items)
        incoming_by_type = self._index_by_type(incoming_items)

        all_types = sorted(set(proposed_by_type.keys()) | set(incoming_by_type.keys()))
        rows: List[Dict[str, Any]] = []

        for schema_type in all_types:
            proposed_type_items = proposed_by_type.get(schema_type, [])
            incoming_type_items = incoming_by_type.get(schema_type, [])

            proposed_attrs = self._extract_attribute_set(proposed_type_items)
            incoming_attrs = self._extract_attribute_set(incoming_type_items)

            missing_attributes = sorted(list(proposed_attrs - incoming_attrs))
            extra_attributes = sorted(list(incoming_attrs - proposed_attrs))

            proposed_nodes = {
                self._extract_node_identifier(item)
                for item in proposed_type_items
                if self._extract_node_identifier(item)
            }
            incoming_nodes = {
                self._extract_node_identifier(item)
                for item in incoming_type_items
                if self._extract_node_identifier(item)
            }

            missing_nodes = sorted(list(proposed_nodes - incoming_nodes))
            extra_nodes = sorted(list(incoming_nodes - proposed_nodes))

            status = "ok"
            if not incoming_type_items:
                status = "missing_type"
            elif missing_attributes or missing_nodes:
                status = "partial"
            elif extra_attributes or extra_nodes:
                status = "updated_extra"

            rows.append({
                "schema_type": schema_type,
                "status": status,
                "proposed_items": len(proposed_type_items),
                "incoming_items": len(incoming_type_items),
                "missing_attributes": missing_attributes,
                "extra_attributes": extra_attributes,
                "missing_nodes": missing_nodes,
                "extra_nodes": extra_nodes
            })

        return {
            "rows": rows,
            "summary": {
                "total_types": len(all_types),
                "ok": sum(1 for r in rows if r["status"] == "ok"),
                "partial": sum(1 for r in rows if r["status"] == "partial"),
                "missing_type": sum(1 for r in rows if r["status"] == "missing_type"),
                "updated_extra": sum(1 for r in rows if r["status"] == "updated_extra")
            }
        }

    def _extract_attribute_set(self, items: List[Dict[str, Any]]) -> Set[str]:
        attrs: Set[str] = set()
        for item in items:
            for key in item.keys():
                if isinstance(key, str):
                    attrs.add(key)
        return attrs

    def _extract_node_identifier(self, item: Dict[str, Any]) -> Optional[str]:
        for key in ("@id", "id", "name", "url"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _check_original_integrity(
        self,
        original_items: List[Dict[str, Any]],
        incoming_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verifica que los tipos y propiedades base no se rompan en el nuevo esquema.
        """
        original_by_type = self._index_by_type(original_items)
        incoming_by_type = self._index_by_type(incoming_items)

        missing_original_types = [t for t in original_by_type.keys() if t not in incoming_by_type]
        changed_fields: List[Dict[str, Any]] = []

        for schema_type, original_examples in original_by_type.items():
            incoming_examples = incoming_by_type.get(schema_type, [])
            if not incoming_examples:
                continue

            original_obj = original_examples[0]
            incoming_obj = incoming_examples[0]

            for key, original_value in original_obj.items():
                if key.startswith("@"):
                    continue

                if key in incoming_obj and incoming_obj[key] != original_value:
                    changed_fields.append({
                        "type": schema_type,
                        "field": key,
                        "original": original_value,
                        "incoming": incoming_obj[key]
                    })

        return {
            "is_preserved": len(missing_original_types) == 0,
            "missing_original_types": missing_original_types,
            "changed_fields": changed_fields[:50]
        }

    def _index_by_type(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        indexed: Dict[str, List[Dict[str, Any]]] = {}
        for item in items:
            schema_type = item.get("@type")
            if isinstance(schema_type, list):
                schema_type = next((t for t in schema_type if isinstance(t, str)), None)
            if not isinstance(schema_type, str) or not schema_type.strip():
                schema_type = "Unknown"

            indexed.setdefault(schema_type, []).append(item)

        return indexed


_schema_audit_service: Optional[SchemaAuditService] = None


def get_schema_audit_service() -> SchemaAuditService:
    global _schema_audit_service
    if _schema_audit_service is None:
        _schema_audit_service = SchemaAuditService()
    return _schema_audit_service
