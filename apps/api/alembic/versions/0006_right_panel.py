"""Advanced robot settings and static page section locks.

Revision ID: 0006_right_panel
Revises: 0005_editor_seo
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_right_panel"
down_revision = "0005_editor_seo"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    cols = {col["name"] for col in sa.inspect(bind).get_columns("properties")}
    for field in ("noarchive", "noimageindex", "nosnippet"):
        if field not in cols:
            op.add_column("properties", sa.Column(field, sa.Boolean(), nullable=False, server_default=sa.false()))
    if "static_sections" not in cols:
        op.add_column("properties", sa.Column("static_sections", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))

def downgrade():
    raise RuntimeError("Restore a verified backup before removing saved SEO and section lock settings.")
