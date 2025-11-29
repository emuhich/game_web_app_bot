import sys
from os.path import dirname, abspath

# Ensure app/ is on sys.path so imports work when called from project root
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context
from app.database import Base, database_url
from app.api.models import User, Master, Service, Application  # noqa: F401

config = context.config
# Формируем синхронный URL для миграций из async URL
if database_url.startswith('sqlite+aiosqlite://'):
    sync_url = database_url.replace('+aiosqlite', '')  # sqlite:///db.sqlite3
else:
    sync_url = database_url
config.set_main_option("sqlalchemy.url", sync_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(url)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
