import logging
import pprint
import uuid
from urllib.parse import urlparse

import pytest

from ..fixtures.doc import doc_table, empty_doc_table, populated_doc_table, ingested_doc_table
from ..fixtures.doc_set import doc_set_table, empty_doc_set_table, populated_doc_set_table, readonly_doc_set_table
from ..fixtures.prompt import prompt_table, empty_prompt_table, populated_prompt_table

logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=2, width=120)


@pytest.mark.asyncio
async def test_simple_question(api_server, ingested_doc_table, sql_sessionmaker):
    """Test a simple question to the /answer/ endpoint and validate the response structure."""
    path = '/answer/'

    data = {'input': 'When did deep learning emerge?'}

    resp_type, resp = await api_server.post(path=path, content_type='json', timeout=180.0, data=data)

    assert resp_type == 'json'

    assert 'threadId' in resp
    assert isinstance(resp['threadId'], str)
    try:
        thread_id = uuid.UUID(resp['threadId'])
    except ValueError:
        assert False, f"threadId '{resp['threadId']}' is not a valid UUID"
    assert isinstance(thread_id, uuid.UUID)

    assert 'question' in resp
    assert resp['question'] == data['input']

    assert 'answer' in resp
    assert isinstance(resp['answer'], str)
    assert len(resp['answer']) > 40

    assert 'citations' in resp
    assert isinstance(resp['citations'], list)
    assert len(resp['citations']) > 0

    for citation in resp['citations']:
        assert 'docUuid' in citation
        assert isinstance(citation['docUuid'], str)
        try:
            doc_id = uuid.UUID(citation['docUuid'])
        except ValueError:
            assert False, f"docUuid '{citation['docUuid']}' is not a valid UUID"
        assert isinstance(doc_id, uuid.UUID)

        assert 'fileName' in citation
        assert isinstance(citation['fileName'], str)
        assert len(citation['fileName']) > 5

        assert 'pageNumber' in citation
        assert isinstance(citation['pageNumber'], int)

        assert 'sourceUrl' in citation
        assert isinstance(citation['sourceUrl'], str)
        assert len(citation['sourceUrl']) > 10
        parsed_url = urlparse(citation['sourceUrl'])
        assert all([parsed_url.scheme, parsed_url.netloc]), f"sourceUrl '{citation['sourceUrl']}' is not a valid URL"

        assert 'text' in citation
        assert isinstance(citation['text'], str)
        assert len(citation['text']) > 10


@pytest.mark.asyncio
async def test_simple_thread(api_server, ingested_doc_table, sql_sessionmaker):
    """Test a simple question to the /answer/ endpoint and validate the response structure."""
    path = '/answer/'

    data = {'input': 'When did deep learning emerge?'}

    resp_type, resp = await api_server.post(path=path, content_type='json', timeout=180.0, data=data)

    assert resp_type == 'json'

    assert 'threadId' in resp
    thread_id = resp['threadId']
    assert isinstance(resp['threadId'], str)

    data = {'input': 'What allowed deep learning to emerge?', 'threadId': thread_id}

    resp_type, resp = await api_server.post(path=path, content_type='json', timeout=180.0, data=data)

    assert resp_type == 'json'

    assert 'threadId' in resp
    assert isinstance(resp['threadId'], str)
    try:
        thread_id = uuid.UUID(resp['threadId'])
    except ValueError:
        assert False, f"threadId '{resp['threadId']}' is not a valid UUID"
    assert isinstance(thread_id, uuid.UUID)

    assert 'question' in resp
    assert resp['question'] == data['input']

    assert 'answer' in resp
    assert isinstance(resp['answer'], str)
    assert len(resp['answer']) > 40

    assert 'citations' in resp
    assert isinstance(resp['citations'], list)
    assert len(resp['citations']) > 0

    for citation in resp['citations']:
        assert 'docUuid' in citation
        assert isinstance(citation['docUuid'], str)
        try:
            doc_id = uuid.UUID(citation['docUuid'])
        except ValueError:
            assert False, f"docUuid '{citation['docUuid']}' is not a valid UUID"
        assert isinstance(doc_id, uuid.UUID)

        assert 'fileName' in citation
        assert isinstance(citation['fileName'], str)
        assert len(citation['fileName']) > 5

        assert 'pageNumber' in citation
        assert isinstance(citation['pageNumber'], int)

        assert 'sourceUrl' in citation
        assert isinstance(citation['sourceUrl'], str)
        assert len(citation['sourceUrl']) > 10
        parsed_url = urlparse(citation['sourceUrl'])
        assert all([parsed_url.scheme, parsed_url.netloc]), f"sourceUrl '{citation['sourceUrl']}' is not a valid URL"

        assert 'text' in citation
        assert isinstance(citation['text'], str)
        assert len(citation['text']) > 10
