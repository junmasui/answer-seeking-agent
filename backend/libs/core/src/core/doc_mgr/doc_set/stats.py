import logging

from core_db.doc_mgr.doc_set.stats import get_document_set_stats
from core_public import DocumentSetStats

logger = logging.getLogger(__name__)


def get_document_set_statistics():
    """
    Get statistics about the document sets table.

    Returns a DocumentSetStats object containing the total count of document sets and the last
    update time from the tracking table.
    """
    table_stats = get_document_set_stats()

    return DocumentSetStats(
        document_set_count=table_stats['doc_set_count'], table_updated_time=table_stats['max_update_time']
    )
