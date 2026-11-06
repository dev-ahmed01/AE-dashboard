import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine
from app import Base
config=context.config
if config.config_file_name and config.get_section(config.config_ini_section).get('handlers'):
    fileConfig(config.config_file_name)
url=os.getenv('DATABASE_URL','sqlite:///./accom-local.db')
config.set_main_option('sqlalchemy.url',url.replace('%','%%'))
target_metadata=Base.metadata

def run_online():
    with create_engine(url).connect() as connection:
        context.configure(connection=connection,target_metadata=target_metadata,compare_type=True)
        with context.begin_transaction():context.run_migrations()
if context.is_offline_mode():
    context.configure(url=url,target_metadata=target_metadata,literal_binds=True)
    with context.begin_transaction():context.run_migrations()
else:run_online()
