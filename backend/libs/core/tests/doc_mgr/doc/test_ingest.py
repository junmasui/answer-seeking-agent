import asyncio
import logging
import pprint
import uuid
import os

import pytest
from core_public import DocumentStatus
from sqlalchemy import func, select

logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=2, width=120)


def _get_table_count(auto_mapped_table, sql_sessionmaker):
    """Return count of records in the specified table."""
    with sql_sessionmaker() as session:
        stmt = select(func.count()).select_from(auto_mapped_table)
        result = session.execute(stmt).first()

        count = result[0]

    return count


def _get_doc_set_id(populated_doc_set_table, sql_sessionmaker):
    """Return the ID of the first document set in the 'populated_doc_set_table'."""
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

    data = {'docUuids': [str(doc_id)]}

    path = '/documents/ingest'
    resp_type, resp = await api_server.post(path=path, content_type='json', data=data)

    assert resp_type == 'json'

    task_ids = resp.get('task_ids')

    assert isinstance(task_ids, list)
    assert len(task_ids) == 1

    task = task_ids[0]

    task_id = task.get('task_id')
    doc_uuid = task.get('doc_uuid')

    assert task_id is not None
    assert doc_id == uuid.UUID(doc_uuid)

    await asyncio.sleep(5)

    loop = 0
    while loop < 1800:  # Allow ingestion to take up to 30 minutes
        loop = loop + 1
        await asyncio.sleep(1)

        with sql_sessionmaker() as session:
            stmt = select(populated_doc_table).where(populated_doc_table.id == doc_id)
            result = session.execute(stmt).first()

            status = result[0].status

            # The status column's datatype is a custom Postgres enum. The SQLAlchemy
            # framework cannot convert a custom Postgres datatype into an custom
            # Python type. We must do that conversion.
            #
            # Convert the str value to our custom Python enum type whenever possible.
            if status in DocumentStatus.__members__:
                status = DocumentStatus[status]

        if status in [DocumentStatus.INGESTED, DocumentStatus.ERROR]:
            break

    assert status == DocumentStatus.INGESTED
