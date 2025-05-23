import pytest, pytest_asyncio

from sqlalchemy import select, func, text


def _get_table_count(auto_mapped_table, sql_sessionmaker):
    """Return count of recods in 'tracked_document_sets'"""
    with sql_sessionmaker() as session:
        stmt = select(func.count()).select_from(auto_mapped_table)
        result = session.execute(stmt).first()
        count = result[0]

    return count


def _truncate_table(auto_mapped_table, sql_engine, sql_sessionmaker):
    """Truncate 'tracked_document_sets'."""
    with sql_engine.connect() as conn:
        conn.execute(text(f'TRUNCATE TABLE "{auto_mapped_table.__table__.name}" RESTART IDENTITY CASCADE'))
        conn.commit()

    count = _get_table_count(auto_mapped_table, sql_sessionmaker)

    if count != 0:
        raise ValueError(f'Something went wrong with truncating {auto_mapped_table.__table__.name}')


@pytest.fixture(scope='module')
def doc_set_table(auto_mapped_classes, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'tracked_document_sets'."""
    full_name = 'tracked_document_sets'
    auto_mapped_table = auto_mapped_classes.get(full_name, None)

    if auto_mapped_table is None:
        raise ValueError(f'Table {full_name} is absent')

    # Clean up table before we start: there are rare error scenarios like power outages or out-of-memory
    # errors where clean-up did not occur.
    _truncate_table(auto_mapped_table, sql_engine, sql_sessionmaker)

    try:
        yield auto_mapped_table

    finally:
        # Clean up table after we are done.
        _truncate_table(auto_mapped_table, sql_engine, sql_sessionmaker)


@pytest.fixture(scope='function')
def empty_doc_set_table(doc_set_table, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'tracked_document_sets'."""

    # Clean up table before we start: there are rare error scenarios like power outages or out-of-memory
    # errors where clean-up did not occur.
    _truncate_table(doc_set_table, sql_engine, sql_sessionmaker)

    try:
        yield doc_set_table

    finally:
        # Clean up table after we are done.
        _truncate_table(doc_set_table, sql_engine, sql_sessionmaker)


async def _populate_doc_set_table(doc_set_table, api_server, sql_engine, sql_sessionmaker):
    # Clean up table before we start: there are rare error scenarios like power outages or out-of-memory
    # errors where clean-up did not occur.
    _truncate_table(doc_set_table, sql_engine, sql_sessionmaker)

    path = '/document-sets/'
    is_default = True
    for index in range(3):
        data = {'name': f'doc set {index}', 'status': 'active', 'isNewDocDefault': is_default, 'isPublicViewable': True}
        is_default = False
        resp = await api_server.post(path=path, content_type='json', data=data)

    count = _get_table_count(doc_set_table, sql_sessionmaker)
    if count != 3:
        raise ValueError(f'Something went wrong with {doc_set_table.__table__.name}')


@pytest_asyncio.fixture(scope='function', loop_scope='function')
async def populated_doc_set_table(doc_set_table, api_server, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'tracked_document_sets'."""
    try:
        await _populate_doc_set_table(doc_set_table, api_server, sql_engine, sql_sessionmaker)

        yield doc_set_table

    finally:
        # Clean up table after we are done.
        _truncate_table(doc_set_table, sql_engine, sql_sessionmaker)


@pytest_asyncio.fixture(scope='module', loop_scope='module')
async def readonly_doc_set_table(doc_set_table, api_server, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'tracked_document_sets'."""
    try:
        await _populate_doc_set_table(doc_set_table, api_server, sql_engine, sql_sessionmaker)

        yield doc_set_table

    finally:
        # Clean up table after we are done.
        _truncate_table(doc_set_table, sql_engine, sql_sessionmaker)
