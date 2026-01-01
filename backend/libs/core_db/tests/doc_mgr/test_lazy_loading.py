
import pytest
import uuid
import datetime
from core_db.db_models.doc_mgr import DbTrackedDocument, DbTrackedDocumentSet
from core_public import DocumentStatus
from core_db.doc_mgr.doc.update import update_tracking_record

@pytest.mark.asyncio
async def test_vector_ids_lazy_loading_fix(async_session):
    """
    Regression test for MissingGreenlet error when accessing vector_ids.
    
    The issue was that vector_ids (MutableList of ARRAY) was being deferred,
    causing a synchronous lazy load attempt inside an async session when accessed,
    especially after a status change triggered an autoflush.
    
    The fix involved adding `undefer(DbTrackedDocument.vector_ids)` to the query.
    """
    # Setup
    doc_set_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    
    doc_set = DbTrackedDocumentSet(
        id=doc_set_id, 
        name="test_set_lazy_load", 
        is_new_doc_default=False, 
        is_public_viewable=False
    )
    async_session.add(doc_set)
    
    doc = DbTrackedDocument(
        id=doc_id, 
        document_set_id=doc_set_id,
        status=DocumentStatus.INGESTING,
        filedir="/tmp",
        filename="test.txt",
        size_bytes=100,
        file_modified_time=datetime.datetime.now(),
        source_url="http://example.com",
        content_type="text/plain",
        s3_rel_path="test.txt",
        vector_ids=["a", "b"]
    )
    async_session.add(doc)
    await async_session.commit()
    
    try:
        # Test
        async with update_tracking_record(doc_uuid=doc_id) as updateable_record:
            assert updateable_record is not None
            
            # Modify a field to trigger potential autoflush on next access
            updateable_record.status = DocumentStatus.INGESTED
            
            # Access vector_ids
            # Without the fix (undefer), this would raise MissingGreenlet
            # With the fix, it should work
            vector_ids = updateable_record.vector_ids
            assert vector_ids == ["a", "b"]
            
    finally:
        # Cleanup
        # We need to merge them back into the session to delete because they might be detached
        # or we can just delete by ID
        from sqlalchemy import delete
        await async_session.execute(delete(DbTrackedDocument).where(DbTrackedDocument.id == doc_id))
        await async_session.execute(delete(DbTrackedDocumentSet).where(DbTrackedDocumentSet.id == doc_set_id))
        await async_session.commit()
