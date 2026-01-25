import logging
from typing import Optional

from core_db.db_models import DbTrackedDocumentSet
from core_db.doc_mgr.doc_set.query import list_tracking_document_sets
from core_public import DocumentSet, DocumentSetList, DocumentSetStatus

from .stats import get_document_set_statistics

logger = logging.getLogger(__name__)


async def list_document_sets(
    *,
    name: Optional[str] = None,
    is_default: Optional[bool] = None,
    is_public: Optional[bool] = None,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort_by: Optional[list] = None,
):
    """Return the list of document sets."""
    existing_objs = await list_tracking_document_sets(
        name=name, is_default=is_default, is_public=is_public, start=start, length=length, sort_by=sort_by
    )
    table_stats = await get_document_set_statistics()

    def _to_dict(_x: DbTrackedDocumentSet):
        """Convert database document set record to API response DocumentSet model."""
        return DocumentSet(
            id=_x.id,
            name=_x.name,
            status=DocumentSetStatus.ACTIVE,  # TODO - Replace hardcode with database column
            is_new_doc_default=_x.is_new_doc_default,
            is_public_viewable=_x.is_public_viewable,
            ocr_strategy=_x.ocr_strategy,
        )

    doc_set_list = [_to_dict(x) for x in existing_objs]

    return DocumentSetList(
        document_sets=doc_set_list,
        document_set_count=table_stats.document_set_count,
        table_updated_time=table_stats.table_updated_time,
    )
