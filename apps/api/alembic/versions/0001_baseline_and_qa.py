"""Baseline existing Accom tables, then apply QA-required columns.

Revision ID: 0001_baseline_and_qa
Revises:
Create Date: 2026-11-06
"""
from alembic import op
import sqlalchemy as sa
from app import Base
revision='0001_baseline_and_qa'
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    # The first release used metadata.create_all without an Alembic version.
    # Preserve its existing rows; only create missing tables.
    Base.metadata.create_all(bind=bind)
    changes={
      'users':[
       sa.Column('email_verified',sa.Boolean(),nullable=False,server_default=sa.false()),
       sa.Column('auth_version',sa.Integer(),nullable=False,server_default='1'),
      ],
      'properties':[
       sa.Column('archived',sa.Boolean(),nullable=False,server_default=sa.false()),
       sa.Column('edit_version',sa.Integer(),nullable=False,server_default='1'),
      ],
      'rooms':[
       sa.Column('image_alt',sa.String(length=240),nullable=False,server_default=''),
       sa.Column('image_layout',sa.String(length=15),nullable=False,server_default='regular'),
       sa.Column('edit_version',sa.Integer(),nullable=False,server_default='1'),
      ],
      'enquiries':[
       sa.Column('booking_reference',sa.String(length=120),nullable=False,server_default=''),
       sa.Column('confirmed_at',sa.DateTime(timezone=True),nullable=True),
      ]
    }
    inspector=sa.inspect(bind)
    for table,columns in changes.items():
        existing={c['name'] for c in inspector.get_columns(table)}
        for column in columns:
            if column.name not in existing:
                op.add_column(table,column)
    # Pre-migration accounts must not be considered email-verified merely
    # because they exist. Admin/editor accounts are explicitly activated by
    # the administrator when the authentication policy is deployed.

def downgrade():
    raise RuntimeError('Data-preserving migration is intentionally not reversible. Restore a tested backup.')
