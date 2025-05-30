import pytest
import pytest_asyncio
from sqlalchemy import func, select, text


def _get_table_count(auto_mapped_table, sql_sessionmaker):
    """Return count of recods in 'agent_prompt'"""
    with sql_sessionmaker() as session:
        stmt = select(func.count()).select_from(auto_mapped_table)
        result = session.execute(stmt).first()
        count = result[0]

    return count


def _truncate_table(auto_mapped_table, sql_engine, sql_sessionmaker):
    """Truncate 'agent_prompt'."""
    with sql_engine.connect() as conn:
        conn.execute(text(f'TRUNCATE TABLE "{auto_mapped_table.__table__.name}" RESTART IDENTITY CASCADE'))
        conn.commit()

    count = _get_table_count(auto_mapped_table, sql_sessionmaker)

    if count != 0:
        raise RuntimeError(f'Something went wrong with truncating {auto_mapped_table.__table__.name}')


@pytest.fixture(scope='module')
def prompt_table(auto_mapped_classes, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'agent_prompt'."""
    full_name = 'agent_prompt'
    auto_mapped_table = auto_mapped_classes.get(full_name, None)

    if auto_mapped_table is None:
        raise RuntimeError(f'Table {full_name} is absent')

    # Clean up table before we start: there are rare error scenarios like power outages or out-of-memory
    # errors where clean-up did not occur.
    _truncate_table(auto_mapped_table, sql_engine, sql_sessionmaker)

    try:
        yield auto_mapped_table

    finally:
        # Clean up table after we are done.
        _truncate_table(auto_mapped_table, sql_engine, sql_sessionmaker)


@pytest.fixture(scope='function')
def empty_prompt_table(prompt_table, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'agent_prompt'."""
    # Clean up table before we start: there are rare error scenarios like power outages or out-of-memory
    # errors where clean-up did not occur.
    _truncate_table(prompt_table, sql_engine, sql_sessionmaker)

    try:
        yield prompt_table

    finally:
        # Clean up table after we are done.
        _truncate_table(prompt_table, sql_engine, sql_sessionmaker)


@pytest_asyncio.fixture(scope='function', loop_scope='function')
async def populated_prompt_table(prompt_table, api_server, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'agent_prompt'."""
    # Clean up table before we start: there are rare error scenarios like power outages or out-of-memory
    # errors where clean-up did not occur.
    _truncate_table(prompt_table, sql_engine, sql_sessionmaker)

    try:
        path = '/prompts/'
        for index in range(3):
            data = {
                'name': f'prompt {index}',
                'humanMessage': f'placeholder human message {index}',
                'systemMessage': f'placeholder system message {index}',
                'includeHistory': index % 2 == 0,
            }
            await api_server.post(path=path, content_type='json', data=data)

        count = _get_table_count(prompt_table, sql_sessionmaker)
        if count != 3:
            raise RuntimeError(f'Something went wrong with {prompt_table.__table__.name}')

        yield prompt_table

    finally:
        # Clean up table after we are done.
        _truncate_table(prompt_table, sql_engine, sql_sessionmaker)
