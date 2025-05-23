import logging
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

logger = logging.getLogger(__name__)


def _get_table_count(auto_mapped_table, sql_sessionmaker):
    with sql_sessionmaker() as session:
        stmt = select(func.count()).select_from(auto_mapped_table)
        result = session.execute(stmt).first()

        count = result[0]

    return count


def _get_doc_set_id(readonly_doc_set_table, sql_sessionmaker):
    with sql_sessionmaker() as session:
        stmt = select(readonly_doc_set_table.id, readonly_doc_set_table.name).select_from(readonly_doc_set_table)
        result = session.execute(stmt).first()

        doc_set_id = result[0]

    return doc_set_id


@pytest.mark.asyncio
async def test_insert(api_server, readonly_doc_set_table, empty_doc_table, sql_sessionmaker):
    count = _get_table_count(readonly_doc_set_table, sql_sessionmaker)

    assert count == 3

    doc_set_id = _get_doc_set_id(readonly_doc_set_table, sql_sessionmaker)

    path = '/documents/upload'
    data = {
        'documentSetId': str(doc_set_id),
        'chunkIndex': 0,
        'totalChunks': 1,
        'sourceUrl': f'https://example.test/test-insert-file-1.pdf',
        'contentType': 'application/pdf',
        'downloadTimeUtc': datetime.now(tz=timezone.utc).isoformat(timespec='minutes'),
    }
    files = {'file': (f'test-insert-file-1.pdf', f'not a PDF insert 1')}
    resp = await api_server.post(path=path, content_type='multipart', data=data, files=files)

    count = _get_table_count(empty_doc_table, sql_sessionmaker)

    assert count == 1


@pytest.mark.asyncio
async def test_find(api_server, populated_doc_table, sql_sessionmaker):
    path = '/documents/'
    content_type, resp = await api_server.get(path=path)

    assert content_type == 'json'

    assert resp.get('documentCount') == 3

    doc_sets = resp.get('documents')

    assert isinstance(doc_sets, list)
    assert len(doc_sets) == 3

    books = [
        'A_History_of_Artificial_Intelligence_1950-2025.pdf',
        'A_History_of_Artificial_Intelligence.pdf',
        'The_History_of_Artificial_Intelligence.pdf',
    ]

    for i in range(3):
        assert doc_sets[i].get('name') == books[i]


@pytest.mark.asyncio
async def test_get(api_server, populated_doc_table, sql_sessionmaker):
    with sql_sessionmaker() as session:
        stmt = select(populated_doc_table)
        result = session.execute(stmt).first()

        doc_id = result[0].id


@pytest.mark.asyncio
async def test_update(api_server, populated_doc_table, sql_sessionmaker):
    with sql_sessionmaker() as session:
        stmt = select(populated_doc_table)
        result = session.execute(stmt).first()

        doc_id = result[0].id

    data = {'documentSetId': None}

    path = f'/documents/{doc_id}'
    content_type, resp = await api_server.patch(path=path, content_type='json', data=data)

    assert content_type == 'json'

    count = _get_table_count(populated_doc_table, sql_sessionmaker)

    assert count == 3


@pytest.mark.asyncio
async def test_delete(api_server, populated_doc_table, sql_sessionmaker):
    with sql_sessionmaker() as session:
        stmt = select(populated_doc_table)
        result = session.execute(stmt).first()

        doc_id = result[0].id

    path = f'/documents/{doc_id}'
    content_type, resp = await api_server.delete(path=path)

    assert content_type == 'json'

    count = _get_table_count(populated_doc_table, sql_sessionmaker)

    assert count == 2
