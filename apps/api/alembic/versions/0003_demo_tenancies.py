"""Add demo-status protection and room-level tenancy options.
Revision ID: 0003_demo_tenancies
Revises: 0002_usernames
"""
from alembic import op
import sqlalchemy as sa
revision='0003_demo_tenancies'
down_revision='0002_usernames'
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    p={c['name'] for c in sa.inspect(bind).get_columns('properties')}
    r={c['name'] for c in sa.inspect(bind).get_columns('rooms')}
    if 'is_demo' not in p:
        op.add_column('properties',sa.Column('is_demo',sa.Boolean(),nullable=False,server_default=sa.false()))
    if 'tenancies' not in r:
        op.add_column('rooms',sa.Column('tenancies',sa.JSON(),nullable=False,server_default=sa.text("'[]'")))

def downgrade():
    raise RuntimeError('Restore a verified backup before reversing tenancy schema.')
