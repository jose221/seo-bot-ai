"""
Servicio centralizado para tareas en segundo plano.
Maneja la ejecución de auditorías y comparaciones.
"""
from uuid import UUID
from datetime import datetime
from typing import List, Any

from app.core.database import db_manager
from app.models.webpage import WebPage
from app.models.audit import AuditReport, AuditStatus
from app.models.audit_comparison import AuditComparison, ComparisonStatus
from app.models.audit_schema_review import AuditSchemaReview, SchemaAuditStatus, SchemaAuditSourceType
from app.models.audit_url_validation import AuditUrlValidation, UrlValidationStatus, UrlValidationSourceType
from app.services.audit_engine import get_audit_engine
from app.services.ai_client import get_ai_client
from app.services.cache import Cache
from app.services.seo_analyzer import SEOAnalyzer, filter_open_graph_schemas
from app.services.audit_comparator import get_audit_comparator
from app.services.schema_audit_service import get_schema_audit_service
from app.helpers import extract_domain
from sqlalchemy import String, cast as sql_cast, desc
from sqlalchemy.orm import joinedload
from sqlmodel import select


async def run_audit_task(
    audit_id: UUID,
    webpage: WebPage,
    include_ai: bool,
    token: str
):
    """
    Ejecutar auditoría en segundo plano.
    Centraliza la lógica de ejecución de auditorías.
    """
    audit = None
    _cache = Cache(table_name="audits_reports")

    try:
        # Actualizar estado a IN_PROGRESS
        with db_manager.sync_session_context() as session:
            audit = session.get(AuditReport, audit_id)
            if not audit:
                print(f"❌ No se encontró audit {audit_id}")
                return

            audit.status = AuditStatus.IN_PROGRESS
            session.add(audit)

        print(f"🚀 Iniciando auditoría para {webpage.url}")

        # Ejecutar auditoría con Playwright/Lighthouse
        audit_engine = get_audit_engine()
        req_lighthouse_params = dict(url=webpage.url, instructions=webpage.instructions)
        lighthouse_result = await _cache.loadFromCacheAsync(
            params=req_lighthouse_params,
            prefix="___lighthouse_report___",
            callback_async=audit_engine.run_lighthouse_audit,
            **req_lighthouse_params
        )

        # Análisis de IA si se solicita
        ai_analysis_data = None
        ai_analysis = None
        if include_ai:
            print(f"🤖 Ejecutando análisis de IA...")
            ai_client = get_ai_client()

            try:
                req_ai_analysis_params = dict(url=webpage.url)
                ai_analysis = await _cache.loadFromCacheAsync(
                    params=req_ai_analysis_params,
                    prefix="ai_analysis_",
                    ttl=3600,
                    callback_async=ai_client.analyze_seo_content,
                    html_content=lighthouse_result.get('html_content_raw', ''),
                    lighthouse_data={
                        'performance_score': lighthouse_result.get('performance_score'),
                        'seo_score': lighthouse_result.get('seo_score'),
                        'accessibility_score': lighthouse_result.get('accessibility_score'),
                        'lcp': lighthouse_result.get('lcp'),
                        'cls': lighthouse_result.get('cls')
                    },
                    token=token,
                    **req_ai_analysis_params
                )

                ai_analysis_content = ""

                print(f"🔍 DEBUG AI Analysis Type: {type(ai_analysis)}")
                if isinstance(ai_analysis, dict):
                     print(f"🔍 DEBUG AI Analysis Keys: {ai_analysis.keys()}")
                     ai_analysis_content = ai_analysis.get('content', '')

                     # Fallback si content esta vacio o no existe
                     if not ai_analysis_content and 'analysis' in ai_analysis:
                         ai_analysis_content = ai_analysis.get('analysis', '')

                     # Tokens se extraen mas abajo
                else:
                     ai_analysis_content = str(ai_analysis)

                print(f"🔍 DEBUG AI Content Length: {len(ai_analysis_content)}")

                ai_analysis_data = {
                    'analysis': ai_analysis_content, # GUARDAR SOLO EL TEXTO
                    'generated_at': datetime.utcnow().isoformat(),
                    'model': 'deepseek-v4-flash'
                }
            except Exception as ai_error:
                print(f"⚠️  Error en análisis de IA: {ai_error}")
                ai_analysis_data = {
                    'error': str(ai_error),
                    'status': 'failed'
                }

        # Análisis SEO
        _seo_analyzer = SEOAnalyzer(
            url=extract_domain(webpage.url),
            html_content=lighthouse_result.get('html_content_raw', '')
        )
        seo_analysis = _seo_analyzer.run_full_analysis()

        # Guardar resultados
        with db_manager.sync_session_context() as session:
            audit = session.get(AuditReport, audit_id)
            # lighthouse_result.pop('html_content', None)
            # lighthouse_result.pop('html_content_raw', None)

            if audit:
                audit.performance_score = lighthouse_result.get('performance_score')
                audit.seo_score = lighthouse_result.get('seo_score')
                audit.accessibility_score = lighthouse_result.get('accessibility_score')
                audit.best_practices_score = lighthouse_result.get('best_practices_score')
                audit.lcp = lighthouse_result.get('lcp')
                audit.fid = lighthouse_result.get('fid')
                audit.cls = lighthouse_result.get('cls')
                audit.lighthouse_data = lighthouse_result
                audit.ai_suggestions = ai_analysis_data

                # Extraer tokens si existen
                if isinstance(ai_analysis, dict) and 'usage' in ai_analysis and ai_analysis['usage']:
                     audit.input_tokens = ai_analysis['usage'].get('prompt_tokens', 0)
                     audit.output_tokens = ai_analysis['usage'].get('completion_tokens', 0)

                audit.status = AuditStatus.COMPLETED
                audit.completed_at = datetime.utcnow()
                audit.seo_analysis = seo_analysis

                audit.report_pdf_path = None
                audit.report_word_path = None
                audit.report_excel_path = None

                session.add(audit)

        print(f"✅ Auditoría completada: {audit_id}")
    except Exception as e:
        print(f"❌ Error en auditoría {audit_id}: {str(e)}")
        import traceback
        traceback.print_exc()

        # Guardar estado de error
        try:
            with db_manager.sync_session_context() as session:
                if audit is None:
                    audit = session.get(AuditReport, audit_id)

                if audit:
                    audit.status = AuditStatus.FAILED
                    audit.error_message = str(e)
                    audit.completed_at = datetime.utcnow()
                    session.add(audit)
        except Exception as inner_error:
            print(f"❌ Error al guardar estado de fallo: {inner_error}")


async def run_comparison_task(
    comparison_id: UUID,
    base_web_page_id: UUID,
    competitor_ids: List[UUID],
    include_ai: bool,
    token: str,
    user_id: UUID
):
    """
    Ejecutar comparación de auditorías en segundo plano.
    """
    comparison = None
    _cache = Cache(table_name="audits_reports_compare_")
    documentation_context = None

    try:
        # Actualizar estado a IN_PROGRESS
        with db_manager.sync_session_context() as session:
            comparison = session.get(AuditComparison, comparison_id)
            if not comparison:
                print(f"❌ No se encontró comparison {comparison_id}")
                return

            documentation_context = comparison.documentation_context
            comparison.status = ComparisonStatus.IN_PROGRESS
            session.add(comparison)

        print(f"🚀 Iniciando comparación {comparison_id}")

        # Obtener página base y su auditoría
        with db_manager.sync_session_context() as session:
            base_webpage = session.get(WebPage, base_web_page_id)
            if not base_webpage:
                raise Exception("Página base no encontrada")

            # Obtener última auditoría completada de la página base
            base_audit_stmt = select(AuditReport).options(joinedload(AuditReport.web_page)).where(
                AuditReport.web_page_id == base_web_page_id,
                sql_cast(AuditReport.status, String) == AuditStatus.COMPLETED.value
            ).order_by(desc(AuditReport.created_at)).limit(1)

            base_audit_result = session.execute(base_audit_stmt)
            base_audit = base_audit_result.scalars().first()

            if not base_audit:
                raise Exception(f"No hay auditorías completadas para {base_webpage.url}")

        # Procesar comparaciones
        comparator = get_audit_comparator()
        comparisons = []
        competitors_audit = []
        total_input_tokens = 0
        total_output_tokens = 0

        with db_manager.sync_session_context() as session:
            for competitor_id in competitor_ids:
                try:
                    competitor_webpage = session.get(WebPage, competitor_id)
                    if not competitor_webpage:
                        print(f"⚠️  Target {competitor_id} no encontrado")
                        continue

                    # Obtener auditoría del competidor
                    competitor_audit_stmt = select(AuditReport).options(joinedload(AuditReport.web_page)).where(
                        AuditReport.web_page_id == competitor_id,
                        sql_cast(AuditReport.status, String) == AuditStatus.COMPLETED.value
                    ).order_by(desc(AuditReport.created_at)).limit(1)

                    competitor_audit_result = session.execute(competitor_audit_stmt)
                    competitor_audit = competitor_audit_result.scalars().first()

                    if not competitor_audit:
                        print(f"⚠️  No hay auditoría para {competitor_webpage.url}")
                        continue

                    # Generar comparación
                    comparison_report = comparator.generate_comparison_report(
                        base_audit=base_audit,
                        compare_audit=competitor_audit,
                        base_url=base_webpage.url,
                        compare_url=competitor_webpage.url
                    )

                    # Análisis de IA si se solicita
                    if include_ai and token:
                        try:
                            req_ai_analysis_params = dict(
                                base_url=base_webpage.url,
                                compare_url=competitor_webpage.url,
                                documentation_context=documentation_context
                            )
                            ai_analysis = await _cache.loadFromCacheAsync(
                                params=req_ai_analysis_params,
                                prefix="ai_analysis_compare_",
                                ttl=36000,
                                callback_async=comparator.generate_ai_comparison,
                                **req_ai_analysis_params,
                                base_audit=base_audit,
                                compare_audit=competitor_audit,
                                documentation_context=documentation_context,
                                token=token
                            )
                            # Handle AI response format
                            if isinstance(ai_analysis, dict):
                                content = ai_analysis.get('content', '')
                                usage = ai_analysis.get('usage', {}) or {}
                                total_input_tokens += usage.get('prompt_tokens', 0)
                                total_output_tokens += usage.get('completion_tokens', 0)
                                comparison_report['ai_analysis'] = content
                            else:
                                comparison_report['ai_analysis'] = ai_analysis

                        except Exception as e:
                            print(f"⚠️ Error en IA para {competitor_webpage.url}: {e}")
                            comparison_report['ai_analysis'] = None

                    comparisons.append(comparison_report)
                    competitors_audit.append(competitor_audit)

                except Exception as e:
                    print(f"❌ Error procesando competidor {competitor_id}: {e}")
                    continue

        if not comparisons:
            raise Exception("No se pudieron generar comparaciones")

        # Generar resumen general
        overall_summary = _generate_overall_summary(base_audit, comparisons)

        # Generar comparación de schemas con IA
        ai_schema_comparison_text = ""
        try:
            ai_schema_comparison = await comparator.generate_ai_schema_comparison(
                base_audit=base_audit,
                compare_audits=competitors_audit,
                token=token,
                base_url=base_webpage.url,
                documentation_context=documentation_context
            )

            if isinstance(ai_schema_comparison, dict):
                ai_schema_comparison_text = ai_schema_comparison.get('content', '')
                schema_usage = ai_schema_comparison.get('usage', {}) or {}
                total_input_tokens += schema_usage.get('prompt_tokens', 0)
                total_output_tokens += schema_usage.get('completion_tokens', 0)
            else:
                ai_schema_comparison_text = str(ai_schema_comparison)
        except Exception as e:
             print(f"⚠️ Error generando comparación de schemas con IA: {e}")
             ai_schema_comparison_text = f"No se pudo generar el análisis de IA para schemas debido a un error en el servicio. {e}"

        # Extract base schemas for report
        base_schemas = []
        if base_audit.seo_analysis and 'schema_markup' in base_audit.seo_analysis:
            base_schemas = base_audit.seo_analysis['schema_markup']

        # Construir resultado final
        comparison_result = {
            "base_url": base_webpage.url,
            "comparisons": comparisons,
            "overall_summary": overall_summary,
            "ai_schema_comparison": ai_schema_comparison_text,
            "raw_schemas": {"base": base_schemas}
        }

        # Guardar resultado
        with db_manager.sync_session_context() as session:
            comparison = session.get(AuditComparison, comparison_id)
            if comparison:
                comparison.status = ComparisonStatus.COMPLETED
                comparison.comparison_result = comparison_result
                comparison.completed_at = datetime.utcnow()

                # Guardar tokens
                comparison.input_tokens = total_input_tokens
                comparison.output_tokens = total_output_tokens

                comparison.report_pdf_path = None
                comparison.report_word_path = None
                comparison.report_excel_path = None

                comparison.proposal_report_pdf_path = None
                comparison.proposal_report_word_path = None

                session.add(comparison)

        print(f"✅ Comparación completada: {comparison_id}")
    except Exception as e:
        print(f"❌ Error en comparación {comparison_id}: {str(e)}")
        import traceback
        traceback.print_exc()

        # Guardar estado de error
        try:
            with db_manager.sync_session_context() as session:
                if comparison is None:
                    comparison = session.get(AuditComparison, comparison_id)

                if comparison:
                    comparison.status = ComparisonStatus.FAILED
                    comparison.error_message = str(e)
                    comparison.completed_at = datetime.utcnow()
                    session.add(comparison)
        except Exception as inner_error:
            print(f"❌ Error al guardar estado de fallo: {inner_error}")


async def run_schema_audit_task(
    schema_audit_id: UUID,
    token: str
):
    """
    Ejecutar auditoría de schemas en segundo plano.
    """
    schema_audit = None

    try:
        with db_manager.sync_session_context() as session:
            schema_audit = session.get(AuditSchemaReview, schema_audit_id)
            if not schema_audit:
                print(f"❌ No se encontró schema_audit {schema_audit_id}")
                return

            schema_audit.status = SchemaAuditStatus.IN_PROGRESS
            session.add(schema_audit)

        service = get_schema_audit_service()
        total_input_tokens = 0
        total_output_tokens = 0

        with db_manager.sync_session_context() as session:
            schema_audit = session.get(AuditSchemaReview, schema_audit_id)
            if not schema_audit:
                raise Exception("Schema audit no encontrado")

            original_schema = schema_audit.original_schema_json
            proposed_schema = schema_audit.proposed_schema_json
            incoming_schema = schema_audit.incoming_schema_json

            validations = {
                "original": service.validate_schema_payload(original_schema, "original"),
                "proposed": service.validate_schema_payload(proposed_schema, "proposed"),
                "incoming": service.validate_schema_payload(incoming_schema, "incoming")
            }

            schema_audit.schema_org_validation_result = validations

            if not validations["proposed"]["is_valid"]:
                raise Exception("El esquema propuesto final no es válido o no está presente")
            if not validations["incoming"]["is_valid"]:
                raise Exception("El esquema nuevo recibido no cumple validación base de schema.org")

            structural_result = service.build_structural_comparison(
                original_schema=original_schema,
                proposed_schema=proposed_schema,
                incoming_schema=incoming_schema
            )

            schema_audit.triple_comparison_result = structural_result
            schema_audit.progress_report = {
                "implemented": structural_result.get("delta", {}).get("implemented_from_proposed", []),
                "pending": structural_result.get("delta", {}).get("pending_from_proposed", []),
                "out_of_scope": structural_result.get("delta", {}).get("new_not_in_proposed", []),
                "comparison_table": structural_result.get("comparison_table", {}),
                "original_integrity": structural_result.get("original_integrity", {})
            }

            session.add(schema_audit)

        ai_triple_report = None
        ai_cqrs_model = None

        if schema_audit.include_ai_analysis:
            ai_triple_report = await service.generate_triple_comparison_ai(
                original_schema=schema_audit.original_schema_json,
                proposed_schema=schema_audit.proposed_schema_json,
                incoming_schema=schema_audit.incoming_schema_json,
                structural_result=schema_audit.triple_comparison_result,
                token=token
            )
            usage_1 = ai_triple_report.get("usage", {})
            total_input_tokens += usage_1.get("prompt_tokens", 0)
            total_output_tokens += usage_1.get("completion_tokens", 0)

            ai_cqrs_model = await service.generate_cqrs_solid_model_ai(
                proposed_schema=schema_audit.proposed_schema_json,
                incoming_schema=schema_audit.incoming_schema_json,
                programming_language=schema_audit.programming_language,
                token=token
            )
            usage_2 = ai_cqrs_model.get("usage", {})
            total_input_tokens += usage_2.get("prompt_tokens", 0)
            total_output_tokens += usage_2.get("completion_tokens", 0)

        with db_manager.sync_session_context() as session:
            schema_audit = session.get(AuditSchemaReview, schema_audit_id)
            if not schema_audit:
                raise Exception("Schema audit no encontrado al finalizar")

            ai_report_text = ai_triple_report.get("content", "") if ai_triple_report else ""
            cqrs_text = ai_cqrs_model.get("content", "") if ai_cqrs_model else ""

            schema_audit.cqrs_solid_model_text = cqrs_text
            schema_audit.progress_report = {
                **(schema_audit.progress_report or {}),
                "ai_report": ai_report_text
            }

            schema_audit.report_pdf_path = None
            schema_audit.report_word_path = None
            schema_audit.input_tokens = total_input_tokens
            schema_audit.output_tokens = total_output_tokens
            schema_audit.status = SchemaAuditStatus.COMPLETED
            schema_audit.completed_at = datetime.utcnow()
            session.add(schema_audit)

        print(f"✅ Auditoría de schemas completada: {schema_audit_id}")
    except Exception as e:
        print(f"❌ Error en auditoría de schemas {schema_audit_id}: {e}")
        import traceback
        traceback.print_exc()

        try:
            with db_manager.sync_session_context() as session:
                if schema_audit is None:
                    schema_audit = session.get(AuditSchemaReview, schema_audit_id)

                if schema_audit:
                    schema_audit.status = SchemaAuditStatus.FAILED
                    schema_audit.error_message = str(e)
                    schema_audit.completed_at = datetime.utcnow()
                    session.add(schema_audit)
        except Exception as inner_error:
            print(f"❌ Error al guardar estado de fallo schema audit: {inner_error}")


async def run_url_validation_task(
    validation_id: UUID,
    urls: List[str],
    proposed_schema: Any,
    name_validation: str,
    description_validation: str,
    ai_instruction: str,
    token: str,
):
    """
    Ejecutar validación de schemas por URL en segundo plano.
    Procesa cada URL individualmente con lapsos aleatorios.
    Si una URL falla, continúa con las siguientes.
    """
    import asyncio
    import random
    from app.services.url_validation_service import get_url_validation_service

    validation = None

    try:
        # Actualizar estado a IN_PROGRESS
        with db_manager.sync_session_context() as session:
            validation = session.get(AuditUrlValidation, validation_id)
            if not validation:
                print(f"❌ No se encontró url_validation {validation_id}")
                return
            validation.status = UrlValidationStatus.IN_PROGRESS
            session.add(validation)

        service = get_url_validation_service()
        total_input_tokens = 0
        total_output_tokens = 0
        results = []

        BATCH_SIZE = 5
        total_urls = len(urls)
        chunks = [urls[i:i + BATCH_SIZE] for i in range(0, total_urls, BATCH_SIZE)]

        print(f"🚀 Iniciando validación de {total_urls} URLs en {len(chunks)} grupos de {BATCH_SIZE} — {name_validation}")

        async def _process_single_url(url: str, idx: int) -> tuple:
            """Procesa una URL y devuelve (result_entry, input_tokens, output_tokens)."""
            print(f"    → [{idx}/{total_urls}] Procesando: {url}")
            result_entry = {"url": url}
            in_tok = 0
            out_tok = 0

            try:
                # 1. Extraer schemas de la URL (con timeout 30s)
                url_schemas = await service.fetch_schema_for_url(url, timeout_ms=30_000)

                if not url_schemas:
                    result_entry["schema_types_found"] = []
                    result_entry["validation_errors"] = {"errors": ["No se detectaron schemas en la URL"]}
                    result_entry["severity"] = "warning"
                    result_entry["ai_report"] = ""
                    result_entry["comparison_table"] = {}
                    print(f"    ⚠️  Sin schemas en {url}")
                    return result_entry, in_tok, out_tok

                # 2. Extraer tipos encontrados
                types_found = []
                url_schemas = filter_open_graph_schemas(url_schemas)

                for schema in url_schemas:
                    if isinstance(schema, dict):
                        stype = schema.get("@type")
                        if isinstance(stype, str):
                            types_found.append(stype)
                        elif isinstance(stype, list):
                            types_found.extend([t for t in stype if isinstance(t, str)])
                        # Buscar en @graph
                        graph = schema.get("@graph", [])
                        if isinstance(graph, list):
                            for node in graph:
                                if isinstance(node, dict):
                                    ntype = node.get("@type")
                                    if isinstance(ntype, str):
                                        types_found.append(ntype)
                                    elif isinstance(ntype, list):
                                        types_found.extend([t for t in ntype if isinstance(t, str)])

                result_entry["schema_types_found"] = sorted(set(types_found))
                result_entry["extracted_schemas"] = url_schemas

                # 3. Validación estructural
                validation_result = service.validate_url_schema(url_schemas, url)
                result_entry["validation_errors"] = validation_result

                # 4. Análisis IA
                try:
                    ai_result = await service.generate_url_analysis_ai(
                        url=url,
                        url_schema=url_schemas,
                        proposed_schema=proposed_schema,
                        validation_errors=validation_result,
                        name_validation=name_validation,
                        description_validation=description_validation,
                        ai_instruction=ai_instruction,
                        token=token,
                    )

                    ai_content = ai_result.get("content", "")
                    usage = ai_result.get("usage", {})
                    in_tok += usage.get("prompt_tokens", 0)
                    out_tok += usage.get("completion_tokens", 0)

                    result_entry["ai_report"] = ai_content
                    result_entry["severity"] = service.extract_severity_from_ai(ai_content)

                except Exception as ai_err:
                    print(f"    ⚠️  Error IA para {url}: {ai_err}")
                    result_entry["ai_report"] = f"Error en análisis IA: {ai_err}"
                    result_entry["severity"] = "warning"

            except Exception as url_err:
                print(f"    ❌ Error procesando {url}: {url_err}")
                result_entry["error"] = str(url_err)
                result_entry["severity"] = "warning"

            return result_entry, in_tok, out_tok

        # Procesar URLs en grupos de BATCH_SIZE en paralelo
        processed = 0
        for batch_num, chunk in enumerate(chunks, 1):
            print(f"  🔄 Grupo {batch_num}/{len(chunks)}: {len(chunk)} URLs en paralelo")
            tasks = [
                _process_single_url(url, processed + i + 1)
                for i, url in enumerate(chunk)
            ]
            batch_results = await asyncio.gather(*tasks)
            for entry, in_tok, out_tok in batch_results:
                results.append(entry)
                total_input_tokens += in_tok
                total_output_tokens += out_tok
            processed += len(chunk)

            # Delay entre grupos (no dentro del grupo)
            if batch_num < len(chunks):
                delay = random.uniform(2, 5)
                print(f"  ⏳ Esperando {delay:.1f}s antes del siguiente grupo...")
                await asyncio.sleep(delay)

        # Calcular severidad global
        global_severity = service.compute_global_severity(results)

        global_report_ai_text = ""
        try:
            print(f"🌐 Generando reporte global con IA para {len(results)} URLs...")
            global_ai_result = await service.generate_global_report_ai(
                results=results,
                name_validation=name_validation,
                description_validation=description_validation,
                global_severity=global_severity,
                token=token,
            )

            global_report_ai_text = global_ai_result.get("content", "")
            global_usage = global_ai_result.get("usage", {})
            total_input_tokens += global_usage.get("prompt_tokens", 0)
            total_output_tokens += global_usage.get("completion_tokens", 0)

        except Exception as global_err:
            print(f"⚠️  Error generando reporte global: {global_err}")
            import traceback
            traceback.print_exc()

        # Guardar resultados finales
        with db_manager.sync_session_context() as session:
            validation = session.get(AuditUrlValidation, validation_id)
            if validation:
                validation.status = UrlValidationStatus.COMPLETED
                validation.results_json = results
                validation.global_severity = global_severity
                validation.input_tokens = total_input_tokens
                validation.output_tokens = total_output_tokens
                validation.report_pdf_path = None
                validation.report_word_path = None
                validation.global_report_pdf_path = None
                validation.global_report_word_path = None
                validation.global_report_ai_text = global_report_ai_text
                validation.completed_at = datetime.utcnow()
                session.add(validation)

        print(f"✅ Validación de URLs completada: {validation_id} — Severidad global: {global_severity}")
    except Exception as e:
        print(f"❌ Error en validación de URLs {validation_id}: {e}")
        import traceback
        traceback.print_exc()

        try:
            with db_manager.sync_session_context() as session:
                if validation is None:
                    validation = session.get(AuditUrlValidation, validation_id)
                if validation:
                    validation.status = UrlValidationStatus.FAILED
                    validation.error_message = str(e)
                    validation.completed_at = datetime.utcnow()
                    session.add(validation)
        except Exception as inner_error:
            print(f"❌ Error al guardar estado de fallo url_validation: {inner_error}")


def _generate_overall_summary(base_audit: AuditReport, comparisons: list) -> dict:
    """Generar resumen consolidado de comparaciones"""
    all_performance_scores = [base_audit.performance_score or 0]
    all_seo_scores = [base_audit.seo_score or 0]
    all_accessibility_scores = [base_audit.accessibility_score or 0]
    all_lcp_values = [base_audit.lcp or 0]
    all_cls_values = [base_audit.cls or 0]

    for comp in comparisons:
        perf = comp.get('performance', {}).get('scores', {})
        all_performance_scores.append(perf.get('compare', {}).get('performance_score', 0))
        all_seo_scores.append(perf.get('compare', {}).get('seo_score', 0))
        all_accessibility_scores.append(perf.get('compare', {}).get('accessibility_score', 0))

        cwv = comp.get('performance', {}).get('core_web_vitals', {})
        all_lcp_values.append(cwv.get('compare', {}).get('lcp', 0))
        all_cls_values.append(cwv.get('compare', {}).get('cls', 0))

    base_perf = base_audit.performance_score or 0
    base_seo = base_audit.seo_score or 0

    perf_rank = sum(1 for score in all_performance_scores if score > base_perf) + 1
    seo_rank = sum(1 for score in all_seo_scores if score > base_seo) + 1

    areas_to_improve = []
    if perf_rank > 1:
        areas_to_improve.append("performance")
    if seo_rank > 1:
        areas_to_improve.append("seo")

    all_recommendations = []
    seen_categories = set()
    for comp in comparisons:
        for rec in comp.get('recommendations', []):
            category = rec.get('category', '')
            if category not in seen_categories:
                all_recommendations.append(rec)
                seen_categories.add(category)

    return {
        "total_competitors": len(comparisons),
        "performance_rank": f"{perf_rank}/{len(all_performance_scores)}",
        "seo_rank": f"{seo_rank}/{len(all_seo_scores)}",
        "is_best_performance": perf_rank == 1,
        "is_best_seo": seo_rank == 1,
        "areas_to_improve": areas_to_improve,
        "top_recommendations": all_recommendations[:5],
        "competitive_advantage": {
            "performance_above_average": base_perf > (sum(all_performance_scores) / len(all_performance_scores)),
            "seo_above_average": base_seo > (sum(all_seo_scores) / len(all_seo_scores)),
        }
    }


# ---------------------------------------------------------------------------
# Re-ejecución de una URL individual dentro de una validación existente
# ---------------------------------------------------------------------------

async def run_url_validation_single_url_task(
    validation_id: UUID,
    target_url: str,
    proposed_schema: Any,
    name_validation: str,
    description_validation: str,
    ai_instruction: str,
    token: str,
):
    """
    Vuelve a analizar una única URL dentro de una AuditUrlValidation existente.
    Actualiza solo la entrada correspondiente en results_json y recalcula global_severity.
    El resto de los resultados se conserva intacto.
    """
    from app.services.url_validation_service import get_url_validation_service

    try:
        with db_manager.sync_session_context() as session:
            validation = session.get(AuditUrlValidation, validation_id)
            if not validation:
                print(f"❌ run_url_validation_single_url_task: validación {validation_id} no encontrada")
                return
            validation.status = UrlValidationStatus.IN_PROGRESS
            session.add(validation)

        service = get_url_validation_service()
        print(f"🔁 Re-analizando URL individual: {target_url} — {name_validation}")

        result_entry = {"url": target_url}
        in_tok = 0
        out_tok = 0

        try:
            url_schemas = await service.fetch_schema_for_url(target_url, timeout_ms=30_000)

            if not url_schemas:
                result_entry.update({
                    "schema_types_found": [],
                    "validation_errors": {"errors": ["No se detectaron schemas en la URL"]},
                    "severity": "warning",
                    "ai_report": "",
                    "comparison_table": {},
                })
            else:
                url_schemas = filter_open_graph_schemas(url_schemas)
                types_found = []
                for schema in url_schemas:
                    if isinstance(schema, dict):
                        stype = schema.get("@type")
                        if isinstance(stype, str):
                            types_found.append(stype)
                        elif isinstance(stype, list):
                            types_found.extend([t for t in stype if isinstance(t, str)])
                        for node in schema.get("@graph", []):
                            if isinstance(node, dict):
                                ntype = node.get("@type")
                                if isinstance(ntype, str):
                                    types_found.append(ntype)
                                elif isinstance(ntype, list):
                                    types_found.extend([t for t in ntype if isinstance(t, str)])

                result_entry["schema_types_found"] = sorted(set(types_found))
                result_entry["extracted_schemas"] = url_schemas

                validation_result = service.validate_url_schema(url_schemas, target_url)
                result_entry["validation_errors"] = validation_result

                try:
                    ai_result = await service.generate_url_analysis_ai(
                        url=target_url,
                        url_schema=url_schemas,
                        proposed_schema=proposed_schema,
                        validation_errors=validation_result,
                        name_validation=name_validation,
                        description_validation=description_validation,
                        ai_instruction=ai_instruction,
                        token=token,
                    )
                    ai_content = ai_result.get("content", "")
                    usage = ai_result.get("usage", {})
                    in_tok = usage.get("prompt_tokens", 0)
                    out_tok = usage.get("completion_tokens", 0)
                    result_entry["ai_report"] = ai_content
                    result_entry["severity"] = service.extract_severity_from_ai(ai_content)
                except Exception as ai_err:
                    print(f"⚠️  Error IA para {target_url}: {ai_err}")
                    result_entry["ai_report"] = f"Error en análisis IA: {ai_err}"
                    result_entry["severity"] = "warning"

        except Exception as url_err:
            print(f"❌ Error procesando {target_url}: {url_err}")
            result_entry["error"] = str(url_err)
            result_entry["severity"] = "warning"

        # Actualizar solo la entrada de esa URL en results_json
        with db_manager.sync_session_context() as session:
            validation = session.get(AuditUrlValidation, validation_id)
            if not validation:
                return

            current_results: list = list(validation.results_json or [])

            # Reemplazar la entrada existente o añadirla si no estaba
            updated = False
            for idx, item in enumerate(current_results):
                if isinstance(item, dict) and item.get("url") == target_url:
                    current_results[idx] = result_entry
                    updated = True
                    break
            if not updated:
                current_results.append(result_entry)

            new_global_severity = service.compute_global_severity(current_results)

            validation.results_json = current_results
            validation.global_severity = new_global_severity
            validation.input_tokens = (validation.input_tokens or 0) + in_tok
            validation.output_tokens = (validation.output_tokens or 0) + out_tok
            validation.report_pdf_path = None
            validation.report_word_path = None
            validation.global_report_pdf_path = None
            validation.global_report_word_path = None
            validation.status = UrlValidationStatus.COMPLETED
            validation.completed_at = datetime.utcnow()
            session.add(validation)

        print(f"✅ Re-análisis de URL individual completado: {target_url} — validación {validation_id}")
    except Exception as e:
        print(f"❌ Error en re-análisis de URL individual {validation_id}/{target_url}: {e}")
        import traceback
        traceback.print_exc()
        try:
            with db_manager.sync_session_context() as session:
                validation = session.get(AuditUrlValidation, validation_id)
                if validation:
                    validation.status = UrlValidationStatus.FAILED
                    validation.error_message = str(e)
                    session.add(validation)
        except Exception as inner:
            print(f"❌ Error al guardar estado de fallo: {inner}")
