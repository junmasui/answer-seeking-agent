import logging
from typing import Optional
import uuid
from datetime import datetime

from sqlalchemy import select, func, column
from sqlalchemy.orm import aliased


from ...providers.sql_database import get_sessionmaker
from ...public_models import DocumentSet, DocumentSetList, DocumentSetStatus

from ..model import TrackedDocumentSet

from .stats import get_document_set_statistics

logger = logging.getLogger(__name__)



def get_document_sets(doc_set_uuid_list: list[str | uuid.UUID]):
    """Return tracking records when matched to specified document UUID."""

    def _ensure_uuid(item):
        return uuid.UUID(hex=item) if isinstance(item, str) else item

    doc_set_uuid_list = [_ensure_uuid(item) for item in doc_set_uuid_list]

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:

        stmt = select(TrackedDocumentSet).where(
            TrackedDocumentSet.id.in_(doc_set_uuid_list))
        result = session.execute(stmt)
        existing_objs = result.scalars().all()

    # The returned objects are detached from the closed session.
    return existing_objs


def list_document_sets(*, is_default: Optional[bool] = None, is_public: Optional[bool] = None,
                       start: Optional[int] =None, length: Optional[int] =None):
    """Return the list of document sets.
    """

    existing_objs = _list_tracking_document_sets(is_default=is_default, is_public=is_public, start=start, length=length)
    table_stats = get_document_set_statistics()


    def _to_dict(_x: TrackedDocumentSet):
        return DocumentSet(
            id = _x.id,
            name = _x.name,
            status = DocumentSetStatus.ACTIVE, # TODO - Replace hardcode with database column
            is_new_doc_default = _x.is_new_doc_default,
            is_public_viewable = _x.is_public_viewable
        )

    doc_set_list = [_to_dict(x) for x in existing_objs]

    return DocumentSetList(
        document_sets = doc_set_list,
        document_set_count = table_stats.document_set_count,
        table_updated_time =  table_stats.table_updated_time
    )


def _list_tracking_document_sets(*, is_default: Optional[bool] = None, is_public: Optional[bool] = None,
                                 start: Optional[int] = None, length: Optional[int] = None):
    """Return tracking set when matched to specified document UUID."""

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:

        paginate = start is not None and length is not None

        # When paginating, we add a windowing function to the selected fields.
        core_query = select(TrackedDocumentSet)

        # Apply query filters

        if is_default is not None:
            core_query = core_query.where(TrackedDocumentSet.is_new_doc_default == is_default)
        if is_public is not None:
            core_query = core_query.where(TrackedDocumentSet.is_public_viewable == is_public)

        # Apply pagination if requested
        if paginate:
            # When paginating, we add a windowing function to the selected fields.
            cte_query= core_query.add_columns(
                func.row_number().over(order_by=TrackedDocumentSet.name).label('row_num')
            )

            # Create a CTE from the core query.
            cte = cte_query.cte(name='row_numbered')

            # Alias the CTE
            WindowedTrackedDocumentSet = aliased(element=TrackedDocumentSet, alias=cte)

            # Query the CTE
            query = select(WindowedTrackedDocumentSet).where(
                # NOTE: Use the `column` function to directly reference the CTE column
                #   labeled 'row_num'. The reason is that 'row_num' is not a part of
                #   the model.
                # NOTE: ROW_NUMBER is 1-indexed. ROW_NUMBER is also inclusive.
                column('row_num').between(start + 1, start + length)
            )
        else:
            query = core_query


        result = session.execute(query)
        existing_objs = result.scalars().all()

    # The returned objects are detached from the closed session.
    return existing_objs

