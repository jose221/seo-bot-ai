"""
Servicio para comparación de auditorías SEO.
Analiza diferencias entre dos auditorías y genera recomendaciones.
"""
from typing import Dict, Any, List, Optional
from app.models.audit import AuditReport
from app.services.ai_client import AIClient


class AuditComparator:
    """Servicio para comparar auditorías SEO"""

    def __init__(self):
        self.ai_client = AIClient()

    def compare_schemas(
        self,
        base_schemas: List[Dict[str, Any]],
        compare_schemas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Comparar schemas estructurados entre dos auditorías.

        Args:
            base_schemas: Schemas de la auditoría base
            compare_schemas: Schemas de la auditoría a comparar

        Returns:
            Diccionario con análisis de diferencias
        """
        # Extraer tipos de schemas
        base_types = set()
        compare_types = set()

        for schema in base_schemas:
            schema_type = schema.get('@type', '')
            if isinstance(schema_type, list):
                base_types.update(schema_type)
            else:
                base_types.add(schema_type)

        for schema in compare_schemas:
            schema_type = schema.get('@type', '')
            if isinstance(schema_type, list):
                compare_types.update(schema_type)
            else:
                compare_types.add(schema_type)

        # Analizar diferencias
        missing_schemas = compare_types - base_types
        common_schemas = base_types & compare_types
        unique_to_base = base_types - compare_types

        return {
            "base_schemas": list(base_types),
            "compare_schemas": list(compare_types),
            "missing_in_base": list(missing_schemas),
            "common_schemas": list(common_schemas),
            "unique_to_base": list(unique_to_base),
            "base_count": len(base_schemas),
            "compare_count": len(compare_schemas),
            "completeness_score": (len(common_schemas) / len(compare_types) * 100) if compare_types else 100
        }

    def compare_performance(
        self,
        base_audit: AuditReport,
        compare_audit: AuditReport
    ) -> Dict[str, Any]:
        """
        Comparar métricas de rendimiento entre auditorías.

        Args:
            base_audit: Auditoría base
            compare_audit: Auditoría a comparar

        Returns:
            Diccionario con comparación de métricas
        """
        metrics = {}

        # Comparar scores
        score_comparisons = {}
        for metric in ['performance_score', 'seo_score', 'accessibility_score', 'best_practices_score']:
            base_value = getattr(base_audit, metric, None)
            compare_value = getattr(compare_audit, metric, None)

            if base_value is not None and compare_value is not None:
                difference = base_value - compare_value
                score_comparisons[metric] = {
                    "base": base_value,
                    "compare": compare_value,
                    "difference": difference,
                    "percentage_diff": (difference / compare_value * 100) if compare_value > 0 else 0,
                    "is_better": difference >= 0,
                    "status": self._get_comparison_status(difference)
                }

        # Comparar Core Web Vitals
        cwv_comparisons = {}
        for metric in ['lcp', 'fid', 'cls']:
            base_value = getattr(base_audit, metric, None)
            compare_value = getattr(compare_audit, metric, None)

            if base_value is not None and compare_value is not None:
                # Para CWV, menor es mejor
                difference = compare_value - base_value
                cwv_comparisons[metric] = {
                    "base": base_value,
                    "compare": compare_value,
                    "difference": difference,
                    "is_better": difference > 0,  # Menor es mejor
                    "status": self._get_cwv_status(metric, base_value, compare_value)
                }

        return {
            "scores": score_comparisons,
            "core_web_vitals": cwv_comparisons,
            "overall_better": self._calculate_overall_winner(score_comparisons)
        }

    def compare_seo_analysis(
        self,
        base_audit: AuditReport,
        compare_audit: AuditReport
    ) -> Dict[str, Any]:
        """
        Comparar análisis SEO on-page.

        Args:
            base_audit: Auditoría base
            compare_audit: Auditoría a comparar

        Returns:
            Diccionario con comparación SEO
        """
        base_seo = base_audit.seo_analysis or {}
        compare_seo = compare_audit.seo_analysis or {}

        comparison = {}

        # Comparar estructura on-page
        if 'onpage_seo' in base_seo and 'onpage_seo' in compare_seo:
            base_onpage = base_seo['onpage_seo']
            compare_onpage = compare_seo['onpage_seo']

            comparison['onpage'] = {
                "title_comparison": self._compare_title(
                    base_onpage.get('title', {}),
                    compare_onpage.get('title', {})
                ),
                "meta_description_comparison": self._compare_meta_description(
                    base_onpage.get('meta_description', {}),
                    compare_onpage.get('meta_description', {})
                ),
                "headers_comparison": self._compare_headers(
                    base_onpage.get('headers_structure', {}),
                    compare_onpage.get('headers_structure', {})
                ),
                "links_comparison": self._compare_links(
                    base_onpage.get('links_count', {}),
                    compare_onpage.get('links_count', {})
                )
            }

        # Comparar aspectos técnicos
        if 'technical_seo' in base_seo and 'technical_seo' in compare_seo:
            base_tech = base_seo['technical_seo']
            compare_tech = compare_seo['technical_seo']

            comparison['technical'] = {
                "robots_txt": {
                    "base_exists": base_tech.get('exists', False),
                    "compare_exists": compare_tech.get('exists', False),
                    "base_sitemaps": len(base_tech.get('sitemaps', [])),
                    "compare_sitemaps": len(compare_tech.get('sitemaps', []))
                }
            }

        return comparison

    def generate_comparison_report(
        self,
        base_audit: AuditReport,
        compare_audit: AuditReport,
        base_url: str,
        compare_url: str
    ) -> Dict[str, Any]:
        """
        Generar reporte completo de comparación.

        Args:
            base_audit: Auditoría base
            compare_audit: Auditoría a comparar
            base_url: URL de la página base
            compare_url: URL de la página a comparar

        Returns:
            Reporte completo con análisis estructurado
        """
        # Extraer schemas
        base_schemas = []
        compare_schemas = []

        if base_audit.seo_analysis and 'schema_markup' in base_audit.seo_analysis:
            base_schemas = base_audit.seo_analysis['schema_markup']

        if compare_audit.seo_analysis and 'schema_markup' in compare_audit.seo_analysis:
            compare_schemas = compare_audit.seo_analysis['schema_markup']

        # Realizar comparaciones
        schema_comparison = self.compare_schemas(base_schemas, compare_schemas)
        performance_comparison = self.compare_performance(base_audit, compare_audit)
        seo_comparison = self.compare_seo_analysis(base_audit, compare_audit)

        return {
            "base_url": base_url,
            "compare_url": compare_url,
            "comparison_date": base_audit.created_at.isoformat() if base_audit.created_at else None,
            "summary": {
                "base_audit_id": str(base_audit.id),
                "compare_audit_id": str(compare_audit.id),
                "overall_winner": performance_comparison.get('overall_better', 'tie')
            },
            "performance": performance_comparison,
            "schemas": schema_comparison,
            # Agregamos los schemas crudos para reportes detallados
            "raw_schemas": {
                "base": base_schemas,
                "compare": compare_schemas
            },
            "seo_analysis": seo_comparison,
            "recommendations": self._generate_recommendations(
                schema_comparison,
                performance_comparison,
                seo_comparison
            )
        }

    async def generate_ai_comparison(
        self,
        base_audit: AuditReport,
        compare_audit: AuditReport,
        base_url: str,
        compare_url: str,
        token: str
    ) -> Dict[str, Any]:
        """
        Generar análisis de comparación usando IA.

        Args:
            base_audit: Auditoría base
            compare_audit: Auditoría a comparar
            base_url: URL de la página base
            compare_url: URL de la página a comparar
            token: Token de autenticación

        Returns:
            Dict con análisis (content) y uso de tokens (usage)
        """
        # Extraer schemas
        base_schemas = []
        compare_schemas = []

        if base_audit.seo_analysis and 'schema_markup' in base_audit.seo_analysis:
            base_schemas = base_audit.seo_analysis['schema_markup']

        if compare_audit.seo_analysis and 'schema_markup' in compare_audit.seo_analysis:
            compare_schemas = compare_audit.seo_analysis['schema_markup']

        # Renderizar prompt desde plantilla
        template = self.ai_client.jinja_env.get_template("audit_comparison.jinja")
        prompt_content = template.render(
            base_audit=base_audit,
            compare_audit=compare_audit,
            base_url=base_url,
            compare_url=compare_url,
            base_schemas=base_schemas,
            compare_schemas=compare_schemas
        )

        from app.schemas.ai_schemas import ChatMessage, MessageRole, ChatCompletionRequest

        user_message = ChatMessage(
            role=MessageRole.USER,
            content=prompt_content
        )

        request = ChatCompletionRequest(
            messages=[user_message],
            model="deepseek-chat",
            stream=False,
            tools=["web_search"]
        )

        response = await self.ai_client.chat_completion(request, token)
        return response.get_content()

    # Métodos auxiliares

    async def generate_ai_schema_comparison(
            self,
            base_audit: AuditReport,
            compare_audits: List[AuditReport],
            token: str,
            base_url: str = "NA"
    ):
        template_schemas_compare = self.ai_client.jinja_env.get_template("schemas_markup_comparison.jinja")
        competitors = []
        base_schemas = []

        if base_audit.seo_analysis and 'schema_markup' in base_audit.seo_analysis:
            base_schemas = self._truncate_schemas(base_audit.seo_analysis['schema_markup'])

        for compare_audit in compare_audits:
            if compare_audit.seo_analysis and 'schema_markup' in compare_audit.seo_analysis:
                compare_schemas = self._truncate_schemas(compare_audit.seo_analysis['schema_markup'])
                # Necesitamos la URL del competidor para el reporte
                # Como compare_audits son objetos AuditReport, necesitamos acceder a web_page.url si está cargado
                # O pasarlo como argumento. Por simplicidad, usaremos un placeholder si no está disponible,
                # pero idealmente background_tasks deberia pasar una estructura mejor.
                # Sin embargo, en background_tasks.py pasamos 'competitors_audit' que son AuditReports.
                # Intentemos obtener la URL de alguna manera o usar ID.
                comp_url = "Competidor"
                if hasattr(compare_audit, 'web_page') and compare_audit.web_page:
                    comp_url = compare_audit.web_page.url

                competitors.append({"url": comp_url, "schemas": compare_schemas})

        params = {
            "base_url": base_url,
            "business_type": "Sitio Web", # Generic fallback
            "schemas": base_schemas,
            "competitors": competitors
        }
        prompt_content = template_schemas_compare.render(**params)
        from app.schemas.ai_schemas import ChatMessage, MessageRole, ChatCompletionRequest

        user_message = ChatMessage(
            role=MessageRole.USER,
            content=prompt_content
        )

        request = ChatCompletionRequest(
            messages=[user_message],
            model="deepseek-chat",
            stream=False,
            # tools=["web_search"] # Desactivar web_search para reducir complejidad si ya tenemos los datos
        )

        # Calcular tokens de entrada manualmente
        input_tokens = self.ai_client.count_tokens(prompt_content)

        response = await self.ai_client.chat_completion(request, token)
        content = response.get_content()

        # Calcular tokens de salida manualmente
        output_tokens = self.ai_client.count_tokens(content)

        return {
            "content": content,
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        }

    def _truncate_schemas(self, schemas: List[Dict[str, Any]], max_items: int = 50) -> List[Dict[str, Any]]:
        """
        No trunca schemas. Devuelve todo el contenido para análisis completo.
        Se mantiene la firma para compatibilidad.
        """
        return schemas

    def _get_comparison_status(self, difference: float) -> str:
        """Obtener estado de comparación basado en diferencia"""
        if difference > 5:
            return "much_better"
        elif difference > 0:
            return "better"
        elif difference > -5:
            return "similar"
        elif difference > -10:
            return "worse"
        else:
            return "much_worse"

    def _get_cwv_status(self, metric: str, base_value: float, compare_value: float) -> str:
        """Obtener estado de Core Web Vitals"""
        thresholds = {
            'lcp': {'good': 2500, 'poor': 4000},
            'fid': {'good': 100, 'poor': 300},
            'cls': {'good': 0.1, 'poor': 0.25}
        }

        threshold = thresholds.get(metric, {})
        good = threshold.get('good', 0)
        poor = threshold.get('poor', 0)

        if base_value <= good:
            return "good"
        elif base_value <= poor:
            return "needs_improvement"
        else:
            return "poor"

    def _calculate_overall_winner(self, score_comparisons: Dict[str, Any]) -> str:
        """Calcular ganador general basado en scores"""
        better_count = sum(1 for comp in score_comparisons.values() if comp.get('is_better', False))
        worse_count = len(score_comparisons) - better_count

        if better_count > worse_count:
            return "base"
        elif worse_count > better_count:
            return "compare"
        else:
            return "tie"

    def _compare_title(self, base_title: Dict, compare_title: Dict) -> Dict[str, Any]:
        """Comparar títulos"""
        return {
            "base_length": base_title.get('length', 0),
            "compare_length": compare_title.get('length', 0),
            "base_status": base_title.get('status', 'Unknown'),
            "compare_status": compare_title.get('status', 'Unknown'),
            "recommendation": "optimal" if 50 <= base_title.get('length', 0) <= 60 else "adjust_length"
        }

    def _compare_meta_description(self, base_meta: Dict, compare_meta: Dict) -> Dict[str, Any]:
        """Comparar meta descriptions"""
        return {
            "base_length": base_meta.get('length', 0),
            "compare_length": compare_meta.get('length', 0),
            "base_status": base_meta.get('status', 'Unknown'),
            "compare_status": compare_meta.get('status', 'Unknown'),
            "recommendation": "optimal" if 150 <= base_meta.get('length', 0) <= 160 else "adjust_length"
        }

    def _compare_headers(self, base_headers: Dict, compare_headers: Dict) -> Dict[str, Any]:
        """Comparar estructura de encabezados"""
        base_h1 = base_headers.get('h1', 0)
        compare_h1 = compare_headers.get('h1', 0)

        return {
            "base_structure": base_headers,
            "compare_structure": compare_headers,
            "base_h1_count": base_h1,
            "compare_h1_count": compare_h1,
            "base_h1_status": "good" if base_h1 == 1 else "needs_fix",
            "compare_h1_status": "good" if compare_h1 == 1 else "needs_fix"
        }

    def _compare_links(self, base_links: Dict, compare_links: Dict) -> Dict[str, Any]:
        """Comparar enlaces internos y externos"""
        return {
            "base_total": base_links.get('total', 0),
            "compare_total": compare_links.get('total', 0),
            "base_internal": base_links.get('internal', 0),
            "compare_internal": compare_links.get('internal', 0),
            "base_external": base_links.get('external', 0),
            "compare_external": compare_links.get('external', 0)
        }

    def _generate_recommendations(
        self,
        schema_comparison: Dict[str, Any],
        performance_comparison: Dict[str, Any],
        seo_comparison: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generar recomendaciones basadas en comparaciones"""
        recommendations = []

        # Recomendaciones de schemas
        missing_schemas = schema_comparison.get('missing_in_base', [])
        if missing_schemas:
            recommendations.append({
                "category": "schema_markup",
                "priority": "high",
                "title": "Implementar schemas faltantes",
                "description": f"El sitio comparado tiene {len(missing_schemas)} schemas que no tienes",
                "missing_schemas": missing_schemas,
                "action": "Agregar los schemas estructurados recomendados"
            })

        # Recomendaciones de performance
        scores = performance_comparison.get('scores', {})
        for metric, data in scores.items():
            if not data.get('is_better', True):
                recommendations.append({
                    "category": "performance",
                    "priority": "medium" if abs(data.get('difference', 0)) < 10 else "high",
                    "title": f"Mejorar {metric.replace('_', ' ')}",
                    "description": f"Tu score es {data['difference']:.1f} puntos menor",
                    "current_value": data['base'],
                    "target_value": data['compare'],
                    "action": f"Optimizar para alcanzar score de {data['compare']}"
                })

        # Recomendaciones SEO
        if 'onpage' in seo_comparison:
            headers_comp = seo_comparison['onpage'].get('headers_comparison', {})
            if headers_comp.get('base_h1_status') != 'good':
                recommendations.append({
                    "category": "seo",
                    "priority": "high",
                    "title": "Corregir estructura de H1",
                    "description": "Debe haber exactamente un H1 por página",
                    "current_value": headers_comp.get('base_h1_count', 0),
                    "target_value": 1,
                    "action": "Asegurar un único H1 descriptivo"
                })

        return recommendations


# Singleton
_audit_comparator: Optional[AuditComparator] = None


def get_audit_comparator() -> AuditComparator:
    """Obtener instancia del comparador de auditorías"""
    global _audit_comparator
    if _audit_comparator is None:
        _audit_comparator = AuditComparator()
    return _audit_comparator

