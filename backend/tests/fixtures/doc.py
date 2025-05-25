import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import func, select, text

from core.public_models.doc import DocumentStatus


def _get_table_count(auto_mapped_table, sql_sessionmaker):
    """Return count of recods in 'tracked_documents'"""
    with sql_sessionmaker() as session:
        stmt = select(func.count()).select_from(auto_mapped_table)
        result = session.execute(stmt).first()
        count = result[0]

    return count


def _truncate_table(auto_mapped_table, sql_engine, sql_sessionmaker):
    """Truncate 'tracked_documents'."""
    with sql_engine.connect() as conn:
        conn.execute(text(f'TRUNCATE TABLE "{auto_mapped_table.__table__.name}" RESTART IDENTITY CASCADE'))
        conn.commit()

    count = _get_table_count(auto_mapped_table, sql_sessionmaker)

    if count != 0:
        raise ValueError(f'Something went wrong with truncating {auto_mapped_table.__table__.name}')


@pytest.fixture(scope='module')
def doc_table(auto_mapped_classes, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'tracked_documents'."""
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


@pytest.fixture(scope='function')
def empty_doc_table(doc_table, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'tracked_documents'."""

    # Clean up table before we start: there are rare error scenarios like power outages or out-of-memory
    # errors where clean-up did not occur.
    _truncate_table(doc_table, sql_engine, sql_sessionmaker)

    try:
        yield doc_table

    finally:
        # Clean up table after we are done.
        _truncate_table(doc_table, sql_engine, sql_sessionmaker)


async def populate_doc_table(doc_table, populated_doc_set_table, api_server, sql_engine, sql_sessionmaker):
    """Populate the 'tracked_documents' table with sample data."""
    # Clean up table before we start: there are rare error scenarios like power outages or out-of-memory
    # errors where clean-up did not occur.
    _truncate_table(doc_table, sql_engine, sql_sessionmaker)

    with sql_sessionmaker() as session:
        stmt = select(populated_doc_set_table.id, populated_doc_set_table.name).select_from(populated_doc_set_table)
        result = session.execute(stmt).first()

        doc_set_id = result[0]

    books = [
        'A_History_of_Artificial_Intelligence_1950-2025.pdf',
        'A_History_of_Artificial_Intelligence.pdf',
        'The_History_of_Artificial_Intelligence.pdf',
    ]

    path = '/documents/upload'
    for index in range(3):
        data = {
            'documentSetId': str(doc_set_id),
            'chunkIndex': 0,
            'totalChunks': 1,
            'sourceUrl': f'https://example.test/{books[index]}',
            'contentType': 'application/pdf',
            'downloadTimeUtc': datetime.now(tz=timezone.utc).isoformat(timespec='minutes'),
        }

        book_path = Path('./tests/data') / books[index]
        with book_path.open('rb') as fin:
            content = fin.read()
        files = {'file': (books[index], content)}
        await api_server.post(path=path, content_type='multipart', data=data, files=files)

    count = _get_table_count(doc_table, sql_sessionmaker)
    if count != 3:
        raise ValueError(f'Something went wrong with {doc_table.__table__.name}')


@pytest_asyncio.fixture(scope='function', loop_scope='function')
async def populated_doc_table(doc_table, readonly_doc_set_table, api_server, sql_engine, sql_sessionmaker):
    """Return the SQLAlchemy reflected table 'tracked_documents'."""
    try:
        await populate_doc_table(doc_table, readonly_doc_set_table, api_server, sql_engine, sql_sessionmaker)

        yield doc_table

    finally:
        # Clean up table after we are done.
        _truncate_table(doc_table, sql_engine, sql_sessionmaker)


@pytest_asyncio.fixture(scope='module', loop_scope='module')
async def ingested_doc_table(doc_table, readonly_doc_set_table, api_server, sql_engine, sql_sessionmaker):
    """Ingest the documents uploaded in the populated_doc_table fixture."""

    try:
        await populate_doc_table(doc_table, readonly_doc_set_table, api_server, sql_engine, sql_sessionmaker)

        with sql_sessionmaker() as session:
            stmt = select(doc_table)
            result = session.execute(stmt).fetchall()

            doc_ids = [row[0].id for row in result]

        path = '/documents/ingest'

        data = {'docUuids': [str(doc_id) for doc_id in doc_ids]}

        resp_type, resp = await api_server.post(path=path, content_type='json', data=data)

        assert resp_type == 'json'

        task_ids = resp.get('task_ids')

        if not isinstance(task_ids, list) or len(task_ids) != len(doc_ids):
            raise RuntimeError('Document ingestion did not correctly queue.')

        await asyncio.sleep(5)

        start = time.time()
        delta = 0.0
        while delta < 3600.0:  # Allow ingestion to take up to 60 minutes
            await asyncio.sleep(1)

            with sql_sessionmaker() as session:
                stmt = select(doc_table).where(doc_table.id.in_(doc_ids))
                result = session.execute(stmt).fetchall()

                statuses = [row[0].status for row in result]

                # Convert statuses to DocumentStatus enum if possible
                statuses = [
                    DocumentStatus[status] if status in DocumentStatus.__members__ else status for status in statuses
                ]

            if all(status in [DocumentStatus.INGESTED, DocumentStatus.ERROR] for status in statuses):
                break

            delta = time.time() - start

        if not all(status == DocumentStatus.INGESTED for status in statuses):
            raise RuntimeError(f'Unexpected document status: {statuses}. Expected statuses are INGESTED or ERROR.')

        yield doc_table

    finally:
        # Clean up table after we are done.
        _truncate_table(doc_table, sql_engine, sql_sessionmaker)
