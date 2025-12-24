#!/usr/bin/env python3
"""
Script de verificación para validar la implementación de rutas de reportes.
Verifica que los modelos, schemas y endpoints estén correctamente configurados.
"""

import sys
from pathlib import Path

# Agregar el path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

def verificar_modelos():
    """Verificar que los modelos tienen los campos necesarios"""
    print("🔍 Verificando modelos...")

    from app.models.audit import AuditReport
    from app.models.audit_comparison import AuditComparison

    # Verificar AuditReport
    assert hasattr(AuditReport, 'report_pdf_path'), "❌ AuditReport no tiene report_pdf_path"
    assert hasattr(AuditReport, 'report_excel_path'), "❌ AuditReport no tiene report_excel_path"
    print("  ✅ AuditReport tiene los campos de reportes")

    # Verificar AuditComparison
    assert hasattr(AuditComparison, 'report_pdf_path'), "❌ AuditComparison no tiene report_pdf_path"
    assert hasattr(AuditComparison, 'report_excel_path'), "❌ AuditComparison no tiene report_excel_path"
    print("  ✅ AuditComparison tiene los campos de reportes")

def verificar_schemas():
    """Verificar que los schemas incluyen los campos de reportes"""
    print("\n🔍 Verificando schemas...")

    from app.schemas.audit_schemas import (
        AuditResponse,
        AuditSearchItem,
        ComparisonListItem,
        ComparisonDetailResponse
    )

    # Crear instancia de prueba
    audit_response = AuditResponse(
        id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
        web_page_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
        user_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
        status="completed",
        performance_score=95.5,
        seo_score=98.2,
        accessibility_score=92.1,
        best_practices_score=88.0,
        lcp=1500.0,
        fid=50.0,
        cls=0.05,
        lighthouse_data={},
        ai_suggestions={},
        created_at="2025-12-24T15:30:00Z",
        completed_at="2025-12-24T15:32:00Z",
        error_message=None,
        report_pdf_path="storage/reports/example.com/report.pdf",
        report_excel_path="storage/reports/example.com/report.xlsx"
    )

    assert audit_response.report_pdf_path == "storage/reports/example.com/report.pdf"
    assert audit_response.report_excel_path == "storage/reports/example.com/report.xlsx"
    print("  ✅ AuditResponse acepta campos de reportes")

    # Verificar schema fields
    schema_fields = AuditSearchItem.model_fields
    assert 'report_pdf_path' in schema_fields, "❌ AuditSearchItem no tiene report_pdf_path"
    assert 'report_excel_path' in schema_fields, "❌ AuditSearchItem no tiene report_excel_path"
    print("  ✅ AuditSearchItem tiene los campos de reportes")

    schema_fields = ComparisonListItem.model_fields
    assert 'report_pdf_path' in schema_fields, "❌ ComparisonListItem no tiene report_pdf_path"
    assert 'report_excel_path' in schema_fields, "❌ ComparisonListItem no tiene report_excel_path"
    print("  ✅ ComparisonListItem tiene los campos de reportes")

    schema_fields = ComparisonDetailResponse.model_fields
    assert 'report_pdf_path' in schema_fields, "❌ ComparisonDetailResponse no tiene report_pdf_path"
    assert 'report_excel_path' in schema_fields, "❌ ComparisonDetailResponse no tiene report_excel_path"
    print("  ✅ ComparisonDetailResponse tiene los campos de reportes")

def verificar_endpoints():
    """Verificar que los endpoints existen"""
    print("\n🔍 Verificando endpoints...")

    from app.api.v1.endpoints import downloads

    assert hasattr(downloads, 'router'), "❌ downloads no tiene router"
    print("  ✅ Módulo de descargas configurado")

    # Verificar que el router tiene las rutas
    routes = [route.path for route in downloads.router.routes]
    expected_routes = [
        "/audits/{audit_id}/download/pdf",
        "/audits/{audit_id}/download/excel",
        "/audits/comparisons/{comparison_id}/download/pdf",
        "/audits/comparisons/{comparison_id}/download/excel"
    ]

    for route in expected_routes:
        assert route in routes, f"❌ Ruta {route} no encontrada"

    print("  ✅ Todas las rutas de descarga configuradas")

def verificar_migracion():
    """Verificar que existe el archivo de migración"""
    print("\n🔍 Verificando migración SQL...")

    migration_file = Path(__file__).parent / "bd" / "add_report_paths.sql"
    assert migration_file.exists(), "❌ Archivo de migración no encontrado"
    print("  ✅ Archivo de migración existe")

    # Verificar contenido
    content = migration_file.read_text()
    assert "report_pdf_path" in content, "❌ Migración no incluye report_pdf_path"
    assert "report_excel_path" in content, "❌ Migración no incluye report_excel_path"
    assert "audit_reports" in content, "❌ Migración no incluye tabla audit_reports"
    assert "audit_comparisons" in content, "❌ Migración no incluye tabla audit_comparisons"
    print("  ✅ Migración SQL correctamente definida")

def main():
    """Ejecutar todas las verificaciones"""
    print("=" * 60)
    print("🚀 VERIFICACIÓN DE IMPLEMENTACIÓN: RUTAS DE REPORTES")
    print("=" * 60)

    try:
        verificar_modelos()
        verificar_schemas()
        verificar_endpoints()
        verificar_migracion()

        print("\n" + "=" * 60)
        print("✅ TODAS LAS VERIFICACIONES PASARON EXITOSAMENTE")
        print("=" * 60)
        print("\n📋 Próximos pasos:")
        print("  1. Ejecutar migración: ./run_migration.sh")
        print("  2. Reiniciar la aplicación")
        print("  3. Probar creando una nueva auditoría")
        print("\n")

        return 0

    except AssertionError as e:
        print(f"\n❌ ERROR: {e}")
        print("\n⚠️  La implementación tiene problemas. Por favor revisa.")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

