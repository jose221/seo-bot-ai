"""
Models module - Exporta todos los modelos de base de datos
"""
from app.models.user import User
from app.models.webpage import WebPage
from app.models.audit import AuditReport, AuditStatus
from app.models.audit_comparison import AuditComparison, ComparisonStatus
from app.models.audit_schema_review import AuditSchemaReview, SchemaAuditStatus, SchemaAuditSourceType
from app.models.audit_url_validation import (
    AuditUrlValidation, UrlValidationStatus, UrlValidationSeverity, UrlValidationSourceType
)
from app.models.url_validation_comment import UrlValidationComment, CommentStatus
from app.models.rich_results_report import RichResultsReport, RichResultsReportStatus
from app.models.structured_validation_task import (
    StructuredValidationTask,
    StructuredValidationTaskStatus,
    StructuredValidationInputMode,
)
from app.models.structured_validation_comment import StructuredValidationComment
from app.models.task_execution_log import TaskExecutionLog

__all__ = [
    "User",
    "WebPage",
    "AuditReport",
    "AuditStatus",
    "AuditComparison",
    "ComparisonStatus",
    "AuditSchemaReview",
    "SchemaAuditStatus",
    "SchemaAuditSourceType",
    "AuditUrlValidation",
    "UrlValidationStatus",
    "UrlValidationSeverity",
    "UrlValidationSourceType",
    "UrlValidationComment",
    "CommentStatus",
    "RichResultsReport",
    "RichResultsReportStatus",
    "StructuredValidationTask",
    "StructuredValidationTaskStatus",
    "StructuredValidationInputMode",
    "StructuredValidationComment",
    "TaskExecutionLog",
]
