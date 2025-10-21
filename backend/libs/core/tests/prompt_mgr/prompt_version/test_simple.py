import pytest
from sqlalchemy import func, select


def _get_table_count(auto_mapped_table, sql_sessionmaker):
    """
    Get the total number of records in the specified database table.

    Helper function for testing that executes a COUNT query against the provided SQLAlchemy table
    using the given session maker.
    """
    with sql_sessionmaker() as session:
        stmt = select(func.count()).select_from(auto_mapped_table)
        result = session.execute(stmt).first()

        count = result[0]

    return count


@pytest.mark.asyncio
async def test_insert(api_server, populated_prompt_table, empty_prompt_version_table, sql_sessionmaker):
    """Test inserting a new prompt version for an existing prompt."""
    # Obtain an existing prompt id to attach the prompt version to
    with sql_sessionmaker() as session:
        stmt = select(populated_prompt_table.id)
        result = session.execute(stmt).first()

        prompt_id = result[0]

    path = f'/prompts/{prompt_id}/versions'
    data = {
        'promptId': str(prompt_id),
        'includeHistory': True,
        'humanMessage': 'placeholder human message',
        'systemMessage': 'placeholder system message',
        'status': 'active',
    }
    _resp = await api_server.post(path=path, content_type='json', data=data)

    count = _get_table_count(empty_prompt_version_table, sql_sessionmaker)

    assert count == 1


@pytest.mark.asyncio
async def test_find(api_server, populated_prompt_version_table, populated_prompt_table, sql_sessionmaker):
    """Test listing prompt-version statistics and listing versions for a prompt."""
    # Check overall table statistics
    stats_path = '/prompt-versions/stats'
    resp_type, resp = await api_server.get(path=stats_path)

    assert resp_type == 'json'

    # Fixture inserts 3 versions across prompts
    assert resp.get('promptVersionCount') == 3

    # Now list prompt versions
    list_path = f'/prompt-versions/'
    resp_type, resp = await api_server.get(path=list_path)

    assert resp_type == 'json'

    prompt_versions = resp.get('promptVersions')

    assert isinstance(prompt_versions, list)
    # The fixture creates one version per prompt id used
    assert len(prompt_versions) == 3


@pytest.mark.asyncio
async def test_find_by_prompt_id(api_server, populated_prompt_version_table, populated_prompt_table, sql_sessionmaker):
    """Test listing prompt-version statistics and listing versions for a prompt."""
    # Check overall table statistics
    stats_path = '/prompt-versions/stats'
    resp_type, resp = await api_server.get(path=stats_path)

    assert resp_type == 'json'

    # Fixture inserts 3 versions across prompts
    assert resp.get('promptVersionCount') == 3

    # Now list versions for a specific prompt (first prompt)
    with sql_sessionmaker() as session:
        stmt = select(populated_prompt_table.id, populated_prompt_table.name).select_from(populated_prompt_table)
        result = session.execute(stmt).first()

        prompt_id = result[0]
        prompt_name = result[1]

    list_path = f'/prompt-versions/?promptId={prompt_id}'
    resp_type, resp = await api_server.get(path=list_path)

    assert resp_type == 'json'

    prompt_versions = resp.get('promptVersions')

    assert isinstance(prompt_versions, list)
    # The fixture creates one version per prompt id used
    assert len(prompt_versions) == 1

    assert prompt_versions[0].get('promptName') == prompt_name




@pytest.mark.asyncio
async def test_find_prompt_versions(api_server, populated_prompt_version_table, populated_prompt_table, sql_sessionmaker):
    """Test listing prompt-version statistics and listing versions for a prompt."""
    # Check overall table statistics
    stats_path = '/prompt-versions/stats'
    resp_type, resp = await api_server.get(path=stats_path)

    assert resp_type == 'json'

    # Fixture inserts 3 versions across prompts
    assert resp.get('promptVersionCount') == 3

    # Now list versions for a specific prompt (first prompt)
    with sql_sessionmaker() as session:
        stmt = select(populated_prompt_table.id, populated_prompt_table.name).select_from(populated_prompt_table)
        result = session.execute(stmt).first()

        prompt_id = result[0]
        prompt_name = result[1]

    list_path = f'/prompts/{prompt_id}/versions'
    resp_type, resp = await api_server.get(path=list_path)

    assert resp_type == 'json'

    prompt_versions = resp.get('promptVersions')

    assert isinstance(prompt_versions, list)
    # The fixture creates one version per prompt id used
    assert len(prompt_versions) == 1

    assert prompt_versions[0].get('promptName') == prompt_name

@pytest.mark.asyncio
async def test_get(api_server, populated_prompt_version_table, sql_sessionmaker):
    """No single-item GET endpoint for prompt-versions; ensure fixture provides entries."""
    with sql_sessionmaker() as session:
        stmt = select(populated_prompt_version_table)
        result = session.execute(stmt).first()

        _prompt_version_id = result[0].id

    # There is no GET /prompt-versions/{id} route - this test just ensures a record exists
    assert _prompt_version_id is not None


@pytest.mark.asyncio
async def test_update(api_server, populated_prompt_version_table, sql_sessionmaker):
    """Test updating an existing prompt version."""
    with sql_sessionmaker() as session:
        stmt = select(populated_prompt_version_table)
        result = session.execute(stmt).first()

        prompt_version_id = result[0].id
        prompt_id = result[0].prompt_id

    path = f'/prompts/{prompt_id}/versions/{prompt_version_id}'
    body = {
        'version': 0,
        'humanMessage': 'updated human message',
        'systemMessage': 'updated system message',
    }
    resp_type, _resp = await api_server.patch(path=path, content_type='json', data=body)

    assert resp_type == 'json'

    count = _get_table_count(populated_prompt_version_table, sql_sessionmaker)

    assert count == 3


@pytest.mark.asyncio
async def test_delete(api_server, populated_prompt_version_table, sql_sessionmaker):
    """Test deleting a prompt version."""
    with sql_sessionmaker() as session:
        stmt = select(populated_prompt_version_table)
        result = session.execute(stmt).first()

        prompt_version_id = result[0].id
        prompt_id = result[0].prompt_id

    path = f'/prompts/{prompt_id}/versions/{prompt_version_id}'
    resp_type, _resp = await api_server.delete(path=path)

    assert resp_type == 'json'

    count = _get_table_count(populated_prompt_version_table, sql_sessionmaker)

    assert count == 2
