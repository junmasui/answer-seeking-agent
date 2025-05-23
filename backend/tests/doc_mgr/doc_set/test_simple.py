import pytest
from sqlalchemy import select, func


def _get_table_count(auto_mapped_table, sql_sessionmaker):
    with sql_sessionmaker() as session:
        stmt = select(func.count()).select_from(auto_mapped_table)
        result = session.execute(stmt).first()

    count = result[0]

    return count


@pytest.mark.asyncio
async def test_insert(api_server, populated_doc_set_table, empty_doc_set_table, sql_sessionmaker):
    path = '/document-sets/'
    data = {'name': 'doc set 1', 'status': 'active', 'isNewDocDefault': False, 'isPublicViewable': True}
    resp = await api_server.post(path=path, content_type='json', data=data)

    count = _get_table_count(empty_doc_set_table, sql_sessionmaker)

    assert count == 1


@pytest.mark.asyncio
async def test_find(api_server, populated_doc_set_table, sql_sessionmaker):
    path = '/document-sets/'
    content_type, resp = await api_server.get(path=path)

    assert content_type == 'json'

    assert resp.get('documentSetCount') == 3

    doc_sets = resp.get('documentSets')

    assert isinstance(doc_sets, list)
    assert len(doc_sets) == 3

    for i in range(3):
        assert doc_sets[i].get('name') == f'doc set {i}'


@pytest.mark.asyncio
async def test_get(api_server, populated_doc_set_table, sql_sessionmaker):
    with sql_sessionmaker() as session:
        stmt = select(populated_doc_set_table)
        result = session.execute(stmt).first()

        doc_set_id = result[0].id


@pytest.mark.asyncio
async def test_update(api_server, populated_doc_set_table, sql_sessionmaker):
    with sql_sessionmaker() as session:
        stmt = select(populated_doc_set_table)
        result = session.execute(stmt).first()

        doc_set_id = result[0].id

    path = f'/document-sets/{doc_set_id}'
    data = {'name': 'updated doc set 1'}
    content_type, resp = await api_server.patch(path=path, content_type='json', data=data)

    assert content_type == 'json'


@pytest.mark.asyncio
async def test_delete(api_server, populated_doc_set_table, sql_sessionmaker):
    with sql_sessionmaker() as session:
        stmt = select(populated_doc_set_table)
        result = session.execute(stmt).first()

        doc_set_id = result[0].id

    path = f'/document-sets/{doc_set_id}'
    content_type, resp = await api_server.delete(path=path)

    assert content_type == 'json'

    count = _get_table_count(populated_doc_set_table, sql_sessionmaker)

    assert count == 2
