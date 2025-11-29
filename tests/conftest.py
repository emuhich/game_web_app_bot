import os
import sys
from pathlib import Path
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Ensure project root is on sys.path for `app.*` imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.database import Base
import app.db.database as db_module


@pytest.fixture(scope="session")
async def test_engine():
    # Use in-memory SQLite for fast tests
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    # Create schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def test_session_maker(test_engine):
    return sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True, scope="session")
def patch_db_session_maker(test_session_maker):
    # Patch the global session maker used across DAOs
    db_module.async_session_maker = test_session_maker
    yield

# Optionally set env vars to avoid loading external configs
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "postgres")
os.environ.setdefault("DB_NAME", "postgres")
