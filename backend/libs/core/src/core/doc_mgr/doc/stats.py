import logging

from core_db.doc_mgr.doc.stats import get_tracking_stats
from core_public import DocumentStats

logger = logging.getLogger(__name__)


def get_document_statistics():
    """
    Get statistics about the tracked documents table.

    Returns a DocumentStats object containing the total count of documents and the last update time
    from the tracking table.
    """
    table_stats = get_tracking_stats()

    return DocumentStats(document_count=table_stats['doc_count'], table_updated_time=table_stats['max_update_time'])


