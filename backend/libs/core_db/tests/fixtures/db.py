
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from ..runtime_config import get_test_config

__all__ = ['get_connection_str', 'async_engine', 'async_session']

def get_connection_str():
    """Return the connection string for the PostgreSQL database from the global configuration."""
    config = get_test_config()

    connection_url = config.postgres_answers_connection_url

    # The connection string must use psycopg3!
    if not connection_url.scheme == 'postgresql+psycopg':
        raise RuntimeError("Connection string must use 'postgresql+psycopg' scheme")

    # Convert away from PyDantic's custom type and to Python string.
    return str(connection_url)

@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def async_engine():
    connection_url = get_connection_str()
    engine = create_async_engine(connection_url)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine):
    # expire_on_commit=False is important for async
    session_maker = async_sessionmaker(async_engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
        # Rollback to keep tests isolated if needed, though here we might commit in setup
        await session.rollback()
