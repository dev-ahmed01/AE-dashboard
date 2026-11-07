"""Add independent SEO follow controls and canonical URL override.

Revision ID: 0005_editor_seo
Revises: 0004_page_content
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_editor_seo"
down_revision = "0004_page_content"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("properties")}
    if "nofollow" not in columns:
        op.add_column("properties", sa.Column("nofollow", sa.Boolean(), nullable=False,
                                             server_default=sa.false()))
    if "canonical_override" not in columns:
        op.add_column("properties", sa.Column("canonical_override", sa.Text(), nullable=False,
                                             server_default=sa.text("''")))


def downgrade():
    # Avoid silent loss of user-entered SEO settings.
    raise RuntimeError("Restore a verified backup before reverting property SEO fields.")
