import asyncio
from datetime import datetime, timezone
import logging
import uuid

import pytest
from sqlalchemy import select, func

from core.public_models.doc import DocumentStatus

logger  = logging.getLogger(__name__)

def _get_table_count(auto_mapped_table, sql_sessionmaker):

    with sql_sessionmaker() as session:
        stmt = select(func.count()).select_from(auto_mapped_table)
        result = session.execute(stmt).first()

        count = result[0]

    return count

def _get_doc_set_id(populated_doc_set_table, sql_sessionmaker):
    with sql_sessionmaker() as session:
        stmt = select(populated_doc_set_table.id, populated_doc_set_table.name).select_from(populated_doc_set_table)
        result = session.execute(stmt).first()

        doc_set_id = result[0]

    return doc_set_id

@pytest.mark.asyncio
async def test_ingest(api_server, populated_doc_table, sql_sessionmaker):

    with sql_sessionmaker() as session:
        stmt = select(populated_doc_table)
        result = session.execute(stmt).first()

        doc_id = result[0].id

    data = {
        'docUuids': [ str(doc_id) ] 
    }

    path = f'/documents/ingest'
    content_type, resp = await api_server.post(path=path, content_type='json', data=data)

    assert content_type == 'json'

    task_ids = resp.get('task_ids')

    assert isinstance(task_ids, list)
    assert len(task_ids) == 1

    task = task_ids[0]

    task_id = task.get('task_id')
    doc_uuid = task.get('doc_uuid')

    assert task_id is not None
    assert doc_id == uuid.UUID(doc_uuid)

    await asyncio.sleep(5)

    logger.info('LOOP FOR INGEST')

    loop = 0
    while loop < 30:
        loop = loop + 1
        await asyncio.sleep(1)

        with sql_sessionmaker() as session:
            stmt = select(populated_doc_table).where(populated_doc_table.id == doc_id)
            result = session.execute(stmt).first()

            status = result[0].status

        if status in [DocumentStatus.INGESTED, DocumentStatus.ERROR]:
            break

        # # TODO - Loop instead on direct database call.
        # path = f'/tasks/{task_id}'
        # content_type, resp = await api_server.get(path=path)

        # logger.info('RESPONSE %s\n%s', content_type, resp)

        # if content_type == 'json':
        #     status = resp.get('taskStatus')
        #     if status in ['SUCCESS', 'FAILURE']:
        #         break

    logger.info('DONE INGEST')
