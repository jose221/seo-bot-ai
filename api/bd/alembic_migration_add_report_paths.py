"""Add report paths to audit tables

Revision ID: add_report_paths_001
Revises:
Create Date: 2025-12-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_report_paths_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Agregar columnas a audit_reports
    op.add_column('audit_reports',
        sa.Column('report_pdf_path', sa.String(), nullable=True)
    )
    op.add_column('audit_reports',
        sa.Column('report_excel_path', sa.String(), nullable=True)
    )

    # Agregar columnas a audit_comparisons
    op.add_column('audit_comparisons',
        sa.Column('report_pdf_path', sa.String(), nullable=True)
    )
    op.add_column('audit_comparisons',
        sa.Column('report_excel_path', sa.String(), nullable=True)
    )


def downgrade():
    # Revertir cambios
    op.drop_column('audit_comparisons', 'report_excel_path')
    op.drop_column('audit_comparisons', 'report_pdf_path')
    op.drop_column('audit_reports', 'report_excel_path')
    op.drop_column('audit_reports', 'report_pdf_path')

