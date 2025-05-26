import pytest
from sqlalchemy import func, select


def _get_table_count(auto_mapped_table, sql_sessionmaker):
    """
    Get the total number of records in the specified database table.

    Helper function for testing that executes a COUNT query against
    the provided SQLAlchemy table using the given session maker.
    """
    with sql_sessionmaker() as session:
        stmt = select(func.count()).select_from(auto_mapped_table)
        result = session.execute(stmt).first()

        count = result[0]

    return count


@pytest.mark.asyncio
async def test_insert(api_server, empty_prompt_table, sql_sessionmaker):
    """Test inserting a new prompt."""
    path = '/prompts/'
    data = {
        'name': 'prompt',
        'humanMessage': 'placeholder human message',
        'systemMessage': 'placeholder system message',
    }
    resp = await api_server.post(path=path, content_type='json', data=data)

    count = _get_table_count(empty_prompt_table, sql_sessionmaker)

    assert count == 1


@pytest.mark.asyncio
async def test_find(api_server, populated_prompt_table, sql_sessionmaker):
    """Test finding prompts."""
    path = '/prompts/'
    content_type, resp = await api_server.get(path=path)

    assert content_type == 'json'

    assert resp.get('promptCount') == 3

    prompts = resp.get('prompts')

    assert isinstance(prompts, list)
    assert len(prompts) == 3

    for i in range(3):
        assert prompts[i].get('name') == f'prompt {i}'


@pytest.mark.asyncio
async def test_get(api_server, populated_prompt_table, sql_sessionmaker):
    """Test getting a specific prompt."""
    with sql_sessionmaker() as session:
        stmt = select(populated_prompt_table)
        result = session.execute(stmt).first()

        prompt_id = result[0].id

    pass


@pytest.mark.asyncio
async def test_update(api_server, populated_prompt_table, sql_sessionmaker):
    """Test updating an existing prompt."""
    with sql_sessionmaker() as session:
        stmt = select(populated_prompt_table)
        result = session.execute(stmt).first()

        prompt_id = result[0].id

    path = f'/prompts/{prompt_id}'
    body = {'humanMessage': 'updated human message', 'systemMessage': 'updated system message'}
    content_type, resp = await api_server.patch(path=path, content_type='json', data=body)

    assert content_type == 'json'

    count = _get_table_count(populated_prompt_table, sql_sessionmaker)

    assert count == 3


@pytest.mark.asyncio
async def test_delete(api_server, populated_prompt_table, sql_sessionmaker):
    """Test deleting a prompt."""
    with sql_sessionmaker() as session:
        stmt = select(populated_prompt_table)
        result = session.execute(stmt).first()

        prompt_id = result[0].id

    path = f'/prompts/{prompt_id}'
    content_type, resp = await api_server.delete(path=path)

    assert content_type == 'json'

    count = _get_table_count(populated_prompt_table, sql_sessionmaker)

    assert count == 2
