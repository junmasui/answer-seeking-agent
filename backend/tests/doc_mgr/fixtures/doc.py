from datetime import datetime, timezone
import pytest, pytest_asyncio

from sqlalchemy import select, func, text


def _get_table_count(auto_mapped_table, sql_sessionmaker):
    """Return count of recods in 'tracked_documents'
    """
    with sql_sessionmaker() as session:
        stmt = select(func.count()).select_from(auto_mapped_table)
        result = session.execute(stmt).first()
        count = result[0]

    return count


def _truncate_table(auto_mapped_table, sql_engine, sql_sessionmaker):
    """Truncate 'tracked_documents'.
    """
    with sql_engine.connect() as conn:
        conn.execute(text(f'TRUNCATE TABLE "{auto_mapped_table.__table__.name}" RESTART IDENTITY CASCADE'))
        conn.commit()

    count = _get_table_count(auto_mapped_table, sql_sessionmaker)

    if count != 0:
        raise ValueError(f'Something went wrong with truncating {auto_mapped_table.__table__.name}')


@pytest.fixture(scope="module")
def doc_table(auto_mapped_classes, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'tracked_documents'.
    """
    full_name = 'tracked_documents'
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



@pytest.fixture(scope="function")
def empty_doc_table(doc_table, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'tracked_documents'.
    """

    # Clean up table before we start: there are rare error scenarios like power outages or out-of-memory
    # errors where clean-up did not occur.
    _truncate_table(doc_table, sql_engine, sql_sessionmaker)

    try:

        yield doc_table

    finally:
        # Clean up table after we are done.
        _truncate_table(doc_table, sql_engine, sql_sessionmaker)





@pytest_asyncio.fixture(scope="function")
async def populated_doc_table(doc_table, populated_doc_set_table, api_server, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'tracked_documents'.
    """
    # Clean up table before we start: there are rare error scenarios like power outages or out-of-memory
    # errors where clean-up did not occur.
    _truncate_table(doc_table, sql_engine, sql_sessionmaker)

    with sql_sessionmaker() as session:
        stmt = select(populated_doc_set_table.id, populated_doc_set_table.name).select_from(populated_doc_set_table)
        result = session.execute(stmt).first()

        doc_set_id = result[0]


    try:

        path = '/documents/upload'
        for index in range(3):
            data = {
                'documentSetId': str(doc_set_id),
                'chunkIndex': 0,
                'totalChunks': 1,
                'sourceUrl': f'https://example.test/test-file-{index}.pdf',
                'contentType': 'application/pdf',
                'downloadTimeUtc': datetime.now(tz=timezone.utc).isoformat(timespec='minutes')
            }
            files = {
                'file': ( f'test-file-{index}.pdf', f'not a PDF {index}' )
            }
            resp = await api_server.post(path=path, content_type='multipart', data=data, files=files)

        count = _get_table_count(doc_table, sql_sessionmaker)
        if count != 3:
            raise ValueError(f'Something went wrong with {doc_table.__table__.name}')

        yield doc_table

    finally:
        # Clean up table after we are done.
        _truncate_table(doc_table, sql_engine, sql_sessionmaker)


