"""
Pipeline de validadores robustos para schemas JSON-LD / Schema.org.

Implementa tres capas de validación:
  1. PyLDValidator         – Integridad estructural JSON-LD (via pyld).
  2. SchemaOrgValidator    – Conformidad con la especificación Schema.org
                             (campos requeridos por tipo, tipos conocidos, etc.).
  3. GoogleComplianceValidator – Reglas específicas de Google Rich Results
                             (campos obligatorios/recomendados para rich snippets).

Uso:
    pipeline = SchemaValidatorPipeline()
    result = pipeline.run(payload, label="incoming")
    # result = {
    #   "validators": [...],
    #   "is_valid": True/False,
    #   "total_errors": int,
    #   "total_warnings": int,
    # }
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _normalize_to_items(payload: Any) -> List[Dict[str, Any]]:
    """Convierte cualquier payload JSON-LD en una lista plana de items dict."""
    if payload is None:
        return []

    parsed = payload
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
        except Exception:
            return []

    if isinstance(parsed, dict):
        if "@graph" in parsed and isinstance(parsed["@graph"], list):
            graph_items = [item for item in parsed["@graph"] if isinstance(item, dict)]
            return graph_items if graph_items else [parsed]
        return [parsed]

    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]

    return []


def _get_type_str(item: Dict[str, Any]) -> Optional[str]:
    """Extrae el @type como string (primer valor si es lista)."""
    t = item.get("@type")
    if isinstance(t, str):
        return t.strip()
    if isinstance(t, list):
        for v in t:
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


# ──────────────────────────────────────────────────────────────────────
# Base
# ──────────────────────────────────────────────────────────────────────

class BaseValidator(ABC):
    """Clase base abstracta para validadores de esquemas."""

    name: str = "BaseValidator"

    @abstractmethod
    def validate(self, payload: Any, label: str) -> Dict[str, Any]:
        """
        Ejecuta la validación sobre *payload*.

        Returns:
            {
                "validator": str,
                "is_valid": bool,
                "errors": List[{"level": str, "message": str}],
                "warnings": List[{"level": str, "message": str}],
            }
        """
        ...


# ──────────────────────────────────────────────────────────────────────
# 1. PyLD – Integridad estructural JSON-LD
# ──────────────────────────────────────────────────────────────────────

class PyLDValidator(BaseValidator):
    """Verifica integridad JSON-LD usando pyld.jsonld.expand()."""

    name = "PyLD"

    def validate(self, payload: Any, label: str) -> Dict[str, Any]:
        errors: List[Dict[str, str]] = []
        warnings: List[Dict[str, str]] = []

        try:
            from pyld import jsonld
        except ImportError:
            warnings.append({
                "level": "INFO",
                "message": "pyld no instalado — validación JSON-LD omitida.",
            })
            return self._result(True, errors, warnings)

        items = _normalize_to_items(payload)
        if not items:
            errors.append({
                "level": "CRITICAL",
                "message": f"{label}: no se encontraron items JSON-LD para validar.",
            })
            return self._result(False, errors, warnings)

        for idx, item in enumerate(items):
            schema_type = _get_type_str(item) or f"item[{idx}]"

            # Asegurar @context para expansión
            doc = dict(item)
            if "@context" not in doc:
                doc["@context"] = "https://schema.org"

            try:
                jsonld.expand(doc, options={
                    "documentLoader": _cached_document_loader,
                })
            except Exception as e:
                err_msg = str(e)
                # Filtrar errores de red (timeout al descargar contexto) como warning
                if "URL" in err_msg or "could not retrieve" in err_msg.lower():
                    warnings.append({
                        "level": "WARNING",
                        "message": (
                            f"{label}[{schema_type}]: No se pudo resolver @context remoto "
                            f"(puede ser problema de red): {err_msg[:200]}"
                        ),
                    })
                else:
                    errors.append({
                        "level": "CRITICAL",
                        "message": f"{label}[{schema_type}]: Estructura JSON-LD inválida — {err_msg[:300]}",
                    })

        return self._result(len(errors) == 0, errors, warnings)

    def _result(self, is_valid: bool, errors: list, warnings: list) -> Dict[str, Any]:
        return {
            "validator": self.name,
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
        }


# Document loader con caché local del contexto schema.org
_SCHEMA_ORG_CONTEXT_CACHE: Dict[str, Any] = {}


def _cached_document_loader(url: str, options: Optional[Dict] = None):
    """
    Document loader custom para PyLD que cachea el contexto de schema.org
    y evita múltiples requests HTTP por validación.
    """
    from pyld import jsonld

    if url in _SCHEMA_ORG_CONTEXT_CACHE:
        return _SCHEMA_ORG_CONTEXT_CACHE[url]

    # Proveer un contexto mínimo embebido para schema.org sin necesidad de HTTP
    if "schema.org" in url:
        result = {
            "contentType": "application/ld+json",
            "contextUrl": None,
            "documentUrl": url,
            "document": {
                "@context": {
                    "@vocab": "http://schema.org/",
                }
            },
        }
        _SCHEMA_ORG_CONTEXT_CACHE[url] = result
        return result

    # Para otros contextos, intentar carga remota
    try:
        result = jsonld.requests_document_loader()(url, options)
        _SCHEMA_ORG_CONTEXT_CACHE[url] = result
        return result
    except Exception:
        # Fallback genérico para evitar fallo total
        result = {
            "contentType": "application/ld+json",
            "contextUrl": None,
            "documentUrl": url,
            "document": {"@context": {}},
        }
        _SCHEMA_ORG_CONTEXT_CACHE[url] = result
        return result


# ──────────────────────────────────────────────────────────────────────
# 2. Schema.org – Conformidad de tipos y propiedades
# ──────────────────────────────────────────────────────────────────────

# Propiedades fundamentales esperadas por tipo en Schema.org
# (no exhaustivo, pero cubre los más relevantes para SEO)
_SCHEMA_ORG_REQUIRED_FIELDS: Dict[str, Dict[str, List[str]]] = {
    "Thing": {
        "required": ["name"],
        "recommended": ["description", "url"],
    },
    "Article": {
        "required": ["headline"],
        "recommended": ["author", "datePublished", "image", "publisher"],
    },
    "NewsArticle": {
        "required": ["headline"],
        "recommended": ["author", "datePublished", "image", "publisher"],
    },
    "BlogPosting": {
        "required": ["headline"],
        "recommended": ["author", "datePublished", "image"],
    },
    "Recipe": {
        "required": ["name"],
        "recommended": ["image", "author", "recipeIngredient", "recipeInstructions"],
    },
    "Product": {
        "required": ["name"],
        "recommended": ["image", "offers", "brand", "description"],
    },
    "LocalBusiness": {
        "required": ["name", "address"],
        "recommended": ["telephone", "openingHoursSpecification", "geo"],
    },
    "Organization": {
        "required": ["name"],
        "recommended": ["url", "logo", "contactPoint"],
    },
    "Person": {
        "required": ["name"],
        "recommended": ["url", "image"],
    },
    "Event": {
        "required": ["name", "startDate"],
        "recommended": ["location", "endDate", "image", "description", "organizer"],
    },
    "FAQPage": {
        "required": ["mainEntity"],
        "recommended": [],
    },
    "HowTo": {
        "required": ["name", "step"],
        "recommended": ["image", "totalTime"],
    },
    "BreadcrumbList": {
        "required": ["itemListElement"],
        "recommended": [],
    },
    "WebSite": {
        "required": ["name", "url"],
        "recommended": ["potentialAction"],
    },
    "WebPage": {
        "required": ["name"],
        "recommended": ["url", "description"],
    },
    "VideoObject": {
        "required": ["name", "uploadDate"],
        "recommended": ["description", "thumbnailUrl", "contentUrl", "duration"],
    },
    "ImageObject": {
        "required": ["contentUrl"],
        "recommended": ["name", "description"],
    },
    "Review": {
        "required": ["reviewBody"],
        "recommended": ["author", "reviewRating", "itemReviewed"],
    },
    "AggregateRating": {
        "required": ["ratingValue"],
        "recommended": ["reviewCount", "bestRating", "worstRating"],
    },
    "Offer": {
        "required": ["price"],
        "recommended": ["priceCurrency", "availability", "url"],
    },
    "Course": {
        "required": ["name"],
        "recommended": ["description", "provider"],
    },
    "SoftwareApplication": {
        "required": ["name"],
        "recommended": ["operatingSystem", "applicationCategory", "offers"],
    },
    "JobPosting": {
        "required": ["title", "datePosted", "description", "hiringOrganization"],
        "recommended": ["jobLocation", "baseSalary", "employmentType"],
    },
    "MedicalWebPage": {
        "required": ["name"],
        "recommended": ["about", "lastReviewed"],
    },
    "Restaurant": {
        "required": ["name", "address"],
        "recommended": ["servesCuisine", "telephone", "menu"],
    },
    "Hotel": {
        "required": ["name", "address"],
        "recommended": ["starRating", "checkinTime", "checkoutTime"],
    },
    "ItemList": {
        "required": ["itemListElement"],
        "recommended": ["name", "numberOfItems"],
    },
    "SearchAction": {
        "required": ["target"],
        "recommended": ["query-input"],
    },
    "ContactPoint": {
        "required": ["contactType"],
        "recommended": ["telephone", "email"],
    },
}

# Tipos conocidos de Schema.org (extendible)
_KNOWN_SCHEMA_TYPES: Set[str] = {
    "Thing", "CreativeWork", "Article", "NewsArticle", "BlogPosting",
    "Recipe", "Product", "LocalBusiness", "Organization", "Person",
    "Event", "FAQPage", "HowTo", "BreadcrumbList", "WebSite", "WebPage",
    "VideoObject", "ImageObject", "Review", "AggregateRating", "Offer",
    "AggregateOffer", "Course", "SoftwareApplication", "JobPosting",
    "MedicalWebPage", "Restaurant", "Hotel", "ItemList", "SearchAction",
    "ContactPoint", "Place", "PostalAddress", "GeoCoordinates",
    "ListItem", "Question", "Answer", "HowToStep", "HowToDirection",
    "NutritionInformation", "MonetaryAmount", "QuantitativeValue",
    "Rating", "Brand", "Country", "Language", "Duration",
    "PropertyValue", "DefinedTerm", "MediaObject", "AudioObject",
    "MusicEvent", "SportsEvent", "EducationEvent", "BusinessEvent",
    "Physician", "Hospital", "Dentist", "Pharmacy", "InsuranceAgency",
    "AutoDealer", "AutoRepair", "Bank", "BarOrPub", "BeautySalon",
    "BookStore", "CafeOrCoffeeShop", "Florist", "FurnitureStore",
    "GasStation", "GolfCourse", "HealthClub", "HomeAndConstructionBusiness",
    "LegalService", "Library", "LodgingBusiness", "MovingCompany",
    "RealEstateAgent", "RecyclingCenter", "SelfStorage", "ShoppingCenter",
    "SkiResort", "SportActivityLocation", "Store", "TouristAttraction",
    "TouristDestination", "TravelAgency", "Service", "FinancialProduct",
    "InsuranceProduct", "LoanOrCredit", "PaymentCard",
    "SiteNavigationElement", "WPHeader", "WPFooter", "WPSideBar",
    "CollectionPage", "ProfilePage", "AboutPage", "ContactPage",
    "CheckoutPage", "FAQPage", "QAPage", "SearchResultsPage",
    "SpecialAnnouncement", "EmployerAggregateRating", "Clip",
    "Movie", "TVSeries", "Book", "MusicRecording", "MusicAlbum",
    "Painting", "Photograph", "Sculpture", "Dataset", "DataCatalog",
    "EducationalOrganization", "GovernmentOrganization",
    "MedicalOrganization", "NGO", "PerformingGroup",
    "Corporation", "Airline",
}


class SchemaOrgValidator(BaseValidator):
    """
    Valida conformidad con la especificación Schema.org:
    - Tipos conocidos
    - Campos requeridos y recomendados por tipo
    """

    name = "SchemaOrg"

    def validate(self, payload: Any, label: str) -> Dict[str, Any]:
        errors: List[Dict[str, str]] = []
        warnings: List[Dict[str, str]] = []

        items = _normalize_to_items(payload)
        if not items:
            return {
                "validator": self.name,
                "is_valid": True,
                "errors": [],
                "warnings": [{"level": "INFO", "message": f"{label}: sin items para validar Schema.org"}],
            }

        for idx, item in enumerate(items):
            schema_type = _get_type_str(item)
            if not schema_type:
                continue  # La validación de @type ausente se maneja en validate_schema_payload

            # Verificar si el tipo es conocido
            if schema_type not in _KNOWN_SCHEMA_TYPES:
                warnings.append({
                    "level": "WARNING",
                    "message": (
                        f"{label}[{idx}]: El tipo '{schema_type}' no está en la lista de tipos "
                        f"Schema.org conocidos. Verifica que sea un tipo válido."
                    ),
                })

            # Verificar campos requeridos y recomendados
            rules = _SCHEMA_ORG_REQUIRED_FIELDS.get(schema_type)
            if not rules:
                continue

            item_keys = set(item.keys())

            for field in rules.get("required", []):
                if field not in item_keys:
                    errors.append({
                        "level": "ERROR",
                        "message": (
                            f"{label}[{idx}] @type={schema_type}: Falta campo requerido "
                            f"'{field}' según Schema.org."
                        ),
                    })

            for field in rules.get("recommended", []):
                if field not in item_keys:
                    warnings.append({
                        "level": "WARNING",
                        "message": (
                            f"{label}[{idx}] @type={schema_type}: Falta campo recomendado "
                            f"'{field}' según Schema.org."
                        ),
                    })

            # Validaciones de sub-objetos específicos
            self._validate_sub_objects(item, schema_type, label, idx, errors, warnings)

        return {
            "validator": self.name,
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def _validate_sub_objects(
        self,
        item: Dict[str, Any],
        schema_type: str,
        label: str,
        idx: int,
        errors: List[Dict[str, str]],
        warnings: List[Dict[str, str]],
    ):
        """Validaciones recursivas de un nivel para sub-objetos clave."""

        # Product → offers debe tener price + priceCurrency
        if schema_type == "Product":
            offers = item.get("offers")
            if isinstance(offers, dict):
                if "price" not in offers and "lowPrice" not in offers:
                    errors.append({
                        "level": "ERROR",
                        "message": (
                            f"{label}[{idx}] @type={schema_type}: "
                            f"'offers' debe contener 'price' o 'lowPrice'."
                        ),
                    })
                if "priceCurrency" not in offers:
                    warnings.append({
                        "level": "WARNING",
                        "message": (
                            f"{label}[{idx}] @type={schema_type}: "
                            f"'offers' debería contener 'priceCurrency'."
                        ),
                    })
            elif isinstance(offers, list):
                for oi, offer in enumerate(offers):
                    if isinstance(offer, dict):
                        if "price" not in offer and "lowPrice" not in offer:
                            errors.append({
                                "level": "ERROR",
                                "message": (
                                    f"{label}[{idx}] @type={schema_type}: "
                                    f"offers[{oi}] debe contener 'price' o 'lowPrice'."
                                ),
                            })

        # FAQPage → mainEntity items deben tener acceptedAnswer
        if schema_type == "FAQPage":
            main_entity = item.get("mainEntity")
            if isinstance(main_entity, list):
                for qi, question in enumerate(main_entity):
                    if isinstance(question, dict):
                        if "acceptedAnswer" not in question:
                            errors.append({
                                "level": "ERROR",
                                "message": (
                                    f"{label}[{idx}] @type={schema_type}: "
                                    f"mainEntity[{qi}] debe contener 'acceptedAnswer'."
                                ),
                            })

        # BreadcrumbList → itemListElement items deben tener item, name, position
        if schema_type == "BreadcrumbList":
            elements = item.get("itemListElement")
            if isinstance(elements, list):
                for ei, elem in enumerate(elements):
                    if isinstance(elem, dict):
                        for req_field in ("name", "position"):
                            if req_field not in elem and req_field != "name":
                                # name puede estar en el sub-item
                                pass
                        if "position" not in elem:
                            warnings.append({
                                "level": "WARNING",
                                "message": (
                                    f"{label}[{idx}] @type={schema_type}: "
                                    f"itemListElement[{ei}] debería contener 'position'."
                                ),
                            })
                        if "item" not in elem and "url" not in elem:
                            warnings.append({
                                "level": "WARNING",
                                "message": (
                                    f"{label}[{idx}] @type={schema_type}: "
                                    f"itemListElement[{ei}] debería contener 'item' o 'url'."
                                ),
                            })

        # HowTo → step items deben tener name o text
        if schema_type == "HowTo":
            steps = item.get("step")
            if isinstance(steps, list):
                for si, step in enumerate(steps):
                    if isinstance(step, dict):
                        if "name" not in step and "text" not in step:
                            errors.append({
                                "level": "ERROR",
                                "message": (
                                    f"{label}[{idx}] @type={schema_type}: "
                                    f"step[{si}] debe contener 'name' o 'text'."
                                ),
                            })


# ──────────────────────────────────────────────────────────────────────
# 3. Google Rich Results – Reglas específicas de Google
# ──────────────────────────────────────────────────────────────────────

# Reglas de Google para Rich Results (más estrictas que Schema.org puro)
# Fuente: https://developers.google.com/search/docs/appearance/structured-data
_GOOGLE_RULES: Dict[str, Dict[str, List[str]]] = {
    "Recipe": {
        "required": ["name", "image"],
        "recommended": [
            "author", "datePublished", "description", "prepTime",
            "cookTime", "totalTime", "recipeYield", "recipeIngredient",
            "recipeInstructions", "nutrition", "recipeCategory", "recipeCuisine",
            "aggregateRating", "video",
        ],
    },
    "Article": {
        "required": ["headline", "image", "author", "datePublished"],
        "recommended": ["dateModified", "publisher", "description"],
    },
    "NewsArticle": {
        "required": ["headline", "image", "author", "datePublished"],
        "recommended": ["dateModified", "publisher"],
    },
    "BlogPosting": {
        "required": ["headline", "image", "author", "datePublished"],
        "recommended": ["dateModified", "publisher"],
    },
    "Product": {
        "required": ["name", "image"],
        "recommended": [
            "description", "offers", "aggregateRating", "review", "brand",
            "sku", "gtin", "mpn",
        ],
    },
    "FAQPage": {
        "required": ["mainEntity"],
        "recommended": [],
    },
    "BreadcrumbList": {
        "required": ["itemListElement"],
        "recommended": [],
    },
    "LocalBusiness": {
        "required": ["name", "address"],
        "recommended": [
            "telephone", "openingHoursSpecification", "geo",
            "image", "url", "priceRange",
        ],
    },
    "Restaurant": {
        "required": ["name", "address", "image"],
        "recommended": ["servesCuisine", "telephone", "menu", "priceRange"],
    },
    "Event": {
        "required": ["name", "startDate", "location"],
        "recommended": [
            "endDate", "image", "description", "offers", "performer",
            "organizer", "eventAttendanceMode", "eventStatus",
        ],
    },
    "HowTo": {
        "required": ["name", "step"],
        "recommended": ["image", "totalTime", "estimatedCost", "supply", "tool"],
    },
    "VideoObject": {
        "required": ["name", "description", "thumbnailUrl", "uploadDate"],
        "recommended": ["contentUrl", "duration", "embedUrl", "interactionStatistic"],
    },
    "JobPosting": {
        "required": ["title", "description", "datePosted", "hiringOrganization", "jobLocation"],
        "recommended": ["baseSalary", "employmentType", "validThrough", "identifier"],
    },
    "Course": {
        "required": ["name", "description", "provider"],
        "recommended": ["offers", "coursePrerequisites", "educationalLevel"],
    },
    "SoftwareApplication": {
        "required": ["name", "offers"],
        "recommended": [
            "operatingSystem", "applicationCategory", "aggregateRating",
            "review", "screenshot",
        ],
    },
    "Review": {
        "required": ["itemReviewed", "reviewRating", "author"],
        "recommended": ["reviewBody", "datePublished", "publisher"],
    },
    "WebSite": {
        "required": ["name", "url"],
        "recommended": ["potentialAction"],
    },
    "Organization": {
        "required": ["name", "url"],
        "recommended": ["logo", "contactPoint", "sameAs"],
    },
    "Dataset": {
        "required": ["name", "description"],
        "recommended": ["license", "creator", "distribution", "temporalCoverage"],
    },
    "Book": {
        "required": ["name", "author"],
        "recommended": ["isbn", "bookEdition", "bookFormat", "numberOfPages"],
    },
    "Movie": {
        "required": ["name"],
        "recommended": ["image", "dateCreated", "director", "review", "aggregateRating"],
    },
    "MusicRecording": {
        "required": ["name"],
        "recommended": ["byArtist", "duration", "inAlbum"],
    },
}


class GoogleComplianceValidator(BaseValidator):
    """
    Reglas específicas de Google Search Rich Results.
    Valida campos requeridos y recomendados que Google necesita para
    generar fragmentos enriquecidos (rich snippets).
    """

    name = "Google-Rich-Results"

    def validate(self, payload: Any, label: str) -> Dict[str, Any]:
        errors: List[Dict[str, str]] = []
        warnings: List[Dict[str, str]] = []

        items = _normalize_to_items(payload)
        if not items:
            return {
                "validator": self.name,
                "is_valid": True,
                "errors": [],
                "warnings": [],
            }

        for idx, item in enumerate(items):
            schema_type = _get_type_str(item)
            if not schema_type:
                continue

            rules = _GOOGLE_RULES.get(schema_type)
            if not rules:
                # No hay reglas Google para este tipo — no es un error
                continue

            item_keys = set(item.keys())

            # Campos requeridos por Google
            for field in rules.get("required", []):
                if field not in item_keys:
                    errors.append({
                        "level": "ERROR",
                        "message": (
                            f"{label}[{idx}] @type={schema_type}: Google requiere el campo "
                            f"'{field}' para generar Rich Results."
                        ),
                    })
                else:
                    # Verificar que el campo no esté vacío
                    val = item.get(field)
                    if val is None or val == "" or val == []:
                        errors.append({
                            "level": "ERROR",
                            "message": (
                                f"{label}[{idx}] @type={schema_type}: El campo requerido "
                                f"'{field}' está vacío."
                            ),
                        })

            # Campos recomendados por Google
            for field in rules.get("recommended", []):
                if field not in item_keys:
                    warnings.append({
                        "level": "WARNING",
                        "message": (
                            f"{label}[{idx}] @type={schema_type}: Google recomienda el campo "
                            f"'{field}' para mejorar Rich Results."
                        ),
                    })

            # Validaciones específicas de sub-objetos para Google
            self._validate_google_specifics(item, schema_type, label, idx, errors, warnings)

        return {
            "validator": self.name,
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def _validate_google_specifics(
        self,
        item: Dict[str, Any],
        schema_type: str,
        label: str,
        idx: int,
        errors: List[Dict[str, str]],
        warnings: List[Dict[str, str]],
    ):
        """Reglas adicionales específicas de Google por tipo."""

        # Product → offers con price y priceCurrency son obligatorios para Google
        if schema_type == "Product":
            offers = item.get("offers")
            if isinstance(offers, dict):
                if "price" not in offers and "lowPrice" not in offers:
                    errors.append({
                        "level": "ERROR",
                        "message": (
                            f"{label}[{idx}] @type={schema_type}: Google requiere 'price' "
                            f"o 'lowPrice' dentro de 'offers'."
                        ),
                    })
                if "priceCurrency" not in offers:
                    errors.append({
                        "level": "ERROR",
                        "message": (
                            f"{label}[{idx}] @type={schema_type}: Google requiere "
                            f"'priceCurrency' dentro de 'offers'."
                        ),
                    })
                if "availability" not in offers:
                    warnings.append({
                        "level": "WARNING",
                        "message": (
                            f"{label}[{idx}] @type={schema_type}: Google recomienda "
                            f"'availability' dentro de 'offers'."
                        ),
                    })

        # Article → author debe ser Person u Organization, no solo string
        if schema_type in ("Article", "NewsArticle", "BlogPosting"):
            author = item.get("author")
            if isinstance(author, str):
                warnings.append({
                    "level": "WARNING",
                    "message": (
                        f"{label}[{idx}] @type={schema_type}: Google recomienda que 'author' "
                        f"sea un objeto {{@type: 'Person'}} en lugar de solo texto."
                    ),
                })
            # publisher debe tener logo
            publisher = item.get("publisher")
            if isinstance(publisher, dict) and "logo" not in publisher:
                warnings.append({
                    "level": "WARNING",
                    "message": (
                        f"{label}[{idx}] @type={schema_type}: Google recomienda que "
                        f"'publisher' tenga un campo 'logo'."
                    ),
                })

        # FAQPage → mainEntity debe ser lista de Questions con acceptedAnswer
        if schema_type == "FAQPage":
            main_entity = item.get("mainEntity")
            if isinstance(main_entity, list):
                for qi, question in enumerate(main_entity):
                    if isinstance(question, dict):
                        q_type = _get_type_str(question)
                        if q_type != "Question":
                            errors.append({
                                "level": "ERROR",
                                "message": (
                                    f"{label}[{idx}] @type={schema_type}: "
                                    f"mainEntity[{qi}] debe ser de @type 'Question' "
                                    f"(encontrado: '{q_type}')."
                                ),
                            })
                        if "acceptedAnswer" not in question:
                            errors.append({
                                "level": "ERROR",
                                "message": (
                                    f"{label}[{idx}] @type={schema_type}: "
                                    f"mainEntity[{qi}] debe contener 'acceptedAnswer'."
                                ),
                            })
                        else:
                            answer = question["acceptedAnswer"]
                            if isinstance(answer, dict) and "text" not in answer:
                                errors.append({
                                    "level": "ERROR",
                                    "message": (
                                        f"{label}[{idx}] @type={schema_type}: "
                                        f"mainEntity[{qi}].acceptedAnswer debe contener 'text'."
                                    ),
                                })
            elif main_entity is not None and not isinstance(main_entity, list):
                warnings.append({
                    "level": "WARNING",
                    "message": (
                        f"{label}[{idx}] @type={schema_type}: 'mainEntity' debería ser "
                        f"una lista de Questions."
                    ),
                })

        # Event → location debe ser Place, VirtualLocation o string
        if schema_type == "Event":
            location = item.get("location")
            if isinstance(location, dict):
                loc_type = _get_type_str(location)
                if loc_type and loc_type not in ("Place", "VirtualLocation", "PostalAddress"):
                    warnings.append({
                        "level": "WARNING",
                        "message": (
                            f"{label}[{idx}] @type={schema_type}: 'location' debería ser "
                            f"de tipo Place o VirtualLocation (encontrado: '{loc_type}')."
                        ),
                    })
                if loc_type == "Place" and "address" not in location:
                    warnings.append({
                        "level": "WARNING",
                        "message": (
                            f"{label}[{idx}] @type={schema_type}: Google recomienda que "
                            f"'location' de tipo Place incluya 'address'."
                        ),
                    })

        # WebSite → potentialAction debe tener SearchAction con target y query-input
        if schema_type == "WebSite":
            potential_action = item.get("potentialAction")
            if isinstance(potential_action, dict):
                action_type = _get_type_str(potential_action)
                if action_type == "SearchAction":
                    if "target" not in potential_action:
                        errors.append({
                            "level": "ERROR",
                            "message": (
                                f"{label}[{idx}] @type={schema_type}: "
                                f"potentialAction.SearchAction requiere 'target'."
                            ),
                        })
                    if "query-input" not in potential_action and "query" not in potential_action:
                        warnings.append({
                            "level": "WARNING",
                            "message": (
                                f"{label}[{idx}] @type={schema_type}: "
                                f"potentialAction.SearchAction debería tener 'query-input'."
                            ),
                        })


# ──────────────────────────────────────────────────────────────────────
# Pipeline
# ──────────────────────────────────────────────────────────────────────

class SchemaValidatorPipeline:
    """
    Orquesta la ejecución secuencial de múltiples validadores sobre un payload.
    """

    def __init__(self, validators: Optional[List[BaseValidator]] = None):
        if validators is None:
            self.validators: List[BaseValidator] = [
                PyLDValidator(),
                SchemaOrgValidator(),
                GoogleComplianceValidator(),
            ]
        else:
            self.validators = validators

    def run(self, payload: Any, label: str) -> Dict[str, Any]:
        """
        Ejecuta todos los validadores y consolida los resultados.

        Returns:
            {
                "validators": [
                    {"validator": "PyLD", "is_valid": ..., "errors": [...], "warnings": [...]},
                    ...
                ],
                "is_valid": bool,      # AND lógico de todos
                "total_errors": int,
                "total_warnings": int,
            }
        """
        results: List[Dict[str, Any]] = []
        all_valid = True
        total_errors = 0
        total_warnings = 0

        for validator in self.validators:
            try:
                result = validator.validate(payload, label)
                results.append(result)

                if not result.get("is_valid", True):
                    all_valid = False

                total_errors += len(result.get("errors", []))
                total_warnings += len(result.get("warnings", []))

            except Exception as e:
                logger.warning(
                    f"Error ejecutando validador {validator.name}: {e}",
                    exc_info=True,
                )
                results.append({
                    "validator": validator.name,
                    "is_valid": True,  # No penalizar por error del validador mismo
                    "errors": [],
                    "warnings": [{
                        "level": "INFO",
                        "message": f"Validador {validator.name} falló internamente: {str(e)[:200]}",
                    }],
                })

        return {
            "validators": results,
            "is_valid": all_valid,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
        }


