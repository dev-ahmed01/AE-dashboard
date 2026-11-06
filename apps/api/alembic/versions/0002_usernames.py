"""Add optional unique usernames without changing existing user emails."""
from alembic import op
import sqlalchemy as sa

revision='0002_usernames'
down_revision='0001_baseline_and_qa'
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    insp=sa.inspect(bind)
    columns={x['name'] for x in insp.get_columns('users')}
    if 'username' not in columns:
        op.add_column('users',sa.Column('username',sa.String(40),nullable=True))
    indexes={i['name'] for i in sa.inspect(bind).get_indexes('users')}
    if 'ix_users_username' not in indexes:
        op.create_index('ix_users_username','users',['username'],unique=True)

def downgrade():
    raise RuntimeError('Restore a database backup if a rollback is required')
