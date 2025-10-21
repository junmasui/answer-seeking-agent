import logging

import pytest
import pytest_asyncio
from sqlalchemy import func, select, text

from ..runtime_config import get_test_config

logger = logging.getLogger(__name__)

PROMPT_TABLE_NAME = 'prompt'


def _get_table_count(auto_mapped_table, sql_sessionmaker):
    """Return count of recods in 'prompt'."""
    with sql_sessionmaker() as session:
        stmt = select(func.count()).select_from(auto_mapped_table)
        result = session.execute(stmt).first()
        count = result[0]

    return count

def _dump_table(auto_mapped_table, sql_sessionmaker):
    """Return table."""
    with sql_sessionmaker() as session:
        stmt = select(auto_mapped_table)
        rows = session.execute(stmt).mappings().all()
        result = [{k: v for k, v in row.items()} for row in rows]

    return result


def _truncate_table(auto_mapped_table, sql_engine, sql_sessionmaker, force: bool = False):
    """Truncate 'prompt'."""
    if not force:
        config = get_test_config()
        if config.skip_tear_down:
            logger.info('Skipping prompt table truncation')
            return

    with sql_engine.connect() as conn:
        conn.execute(text(f'TRUNCATE TABLE "{auto_mapped_table.__table__.name}" RESTART IDENTITY CASCADE'))
        conn.commit()

    count = _get_table_count(auto_mapped_table, sql_sessionmaker)

    if count != 0:
        raise RuntimeError(f'Something went wrong with truncating {auto_mapped_table.__table__.name}')


@pytest.fixture(scope='module')
def prompt_table(auto_mapped_classes, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'prompt'."""
    auto_mapped_table = auto_mapped_classes.get(PROMPT_TABLE_NAME, None)

    if auto_mapped_table is None:
        raise RuntimeError(f'Table {PROMPT_TABLE_NAME} is absent')

    # Clean up table before we start: there are rare error scenarios like power outages
    # or out-of-memory errors where clean-up did not occur.
    _truncate_table(auto_mapped_table, sql_engine, sql_sessionmaker, force=True)

    try:
        yield auto_mapped_table

    finally:
        # Clean up table after we are done.
        _truncate_table(auto_mapped_table, sql_engine, sql_sessionmaker)


@pytest.fixture(scope='function')
def empty_prompt_table(prompt_table, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'prompt'."""
    # Clean up table before we start: there are rare error scenarios like power outages
    # or out-of-memory errors where clean-up did not occur.
    _truncate_table(prompt_table, sql_engine, sql_sessionmaker, force=True)

    try:
        yield prompt_table

    finally:
        # Clean up table after we are done.
        _truncate_table(prompt_table, sql_engine, sql_sessionmaker)


@pytest_asyncio.fixture(scope='function', loop_scope='function')
async def populated_prompt_table(prompt_table, api_server, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'prompt'."""
    # Clean up table before we start: there are rare error scenarios like power outages
    # or out-of-memory errors where clean-up did not occur.
    count = _get_table_count(prompt_table, sql_sessionmaker)
    _truncate_table(prompt_table, sql_engine, sql_sessionmaker, force=True)

    try:
        path = '/prompts/'
        for index in range(3):
            data = {
                'name': f'prompt {index}'
            }
            await api_server.post(path=path, content_type='json', data=data)

        count = _get_table_count(prompt_table, sql_sessionmaker)

        data = _dump_table(prompt_table, sql_sessionmaker=sql_sessionmaker)

        if count != 3:
            raise RuntimeError(f'Something went wrong with {prompt_table.__table__.name}')

        yield prompt_table

        count = _get_table_count(prompt_table, sql_sessionmaker)

    finally:
        # Clean up table after we are done.
        _truncate_table(prompt_table, sql_engine, sql_sessionmaker)
