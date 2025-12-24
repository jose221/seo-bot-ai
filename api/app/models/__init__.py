"""
Models module - Exporta todos los modelos de base de datos
"""
from app.models.user import User
from app.models.webpage import WebPage
from app.models.audit import AuditReport, AuditStatus
from app.models.audit_comparison import AuditComparison, ComparisonStatus

__all__ = [
    "User",
    "WebPage",
    "AuditReport",
    "AuditStatus",
    "AuditComparison",
    "ComparisonStatus",
]

