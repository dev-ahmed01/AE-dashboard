"""Persist safe per-element master-template copy for all property sections.

Revision ID: 0004_page_content
Revises: 0003_demo_tenancies
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_page_content"
down_revision = "0003_demo_tenancies"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("properties")}
    if "highlight_descriptions" not in columns:
        op.add_column("properties", sa.Column("highlight_descriptions", sa.JSON(),
                                              nullable=False, server_default=sa.text("'[]'")))
    if "content_overrides" not in columns:
        op.add_column("properties", sa.Column("content_overrides", sa.JSON(),
                                              nullable=False, server_default=sa.text("'{}'")))


def downgrade():
    raise RuntimeError("Restore a verified backup before reverting page-copy changes.")
