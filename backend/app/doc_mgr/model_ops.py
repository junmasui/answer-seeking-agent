import logging
from datetime import datetime
import uuid
from contextlib import contextmanager

from sqlalchemy import select, delete, func, column
from sqlalchemy.orm import aliased

from ..providers.sql_database import get_sessionmaker

from .model import TrackedDocument, DocumentStatus, create_tables_if_not_existing


logger = logging.getLogger(__name__)


def generate_uuid_from_name(name):
    namespace = uuid.NAMESPACE_URL

    # Generate the UUID from the namespace and name
    return uuid.uuid5(namespace, name)


def list_tracking_records(start: int, length: int):
    """Return a page of tracking records.
    
    The implementation is an older known-performance technique. The technique
    creates a CTE (alternatively, a subquery could have been used) where each
    row is augmented with the windowing function ROW_NUMBER. Then the rows whose
    ROW_NUMBER values fall into the page range are choosen. Finally, the row
    data minus the ROW_NUMBER values are returned.
    """
    create_tables_if_not_existing()

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:

        # Create a CTE with row numbers assigned to each row.
        cte = select(
            TrackedDocument,
            func.row_number().over(order_by=TrackedDocument.filename).label('row_num')
        ).cte('numbered_rows')

        # Alias the CTE
        numbered_rows = aliased(TrackedDocument, cte)

        # Query the CTE
        query = select(numbered_rows).where(
            # NOTE: Use the `column` function to directly reference the CTE column
            #   labeled 'row_num'. The reason is that 'row_num' is not a part of
            #   the model.
            # NOTE: ROW_NUMBER is 1-indexed. ROW_NUMBER is also inclusive.
            column('row_num').between(start + 1, start + length)
        )

        result = session.execute(query)
        existing_objs = result.scalars().all()

    return existing_objs


def get_tracking_stats():
    """Return the count of records and maximum updated_at time
    in the tracking table.
    """
    create_tables_if_not_existing()

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:
        stmt = select(
            func.count().label('doc_count'),
            func.max(TrackedDocument.updated_at).label('max_updated_at')
        )
        result = session.execute(stmt).first()
    return {
        'doc_count': result[0],
        'max_updated_at': result[1]
    }


def get_tracking_records(doc_uuid_list: list[str | uuid.UUID]):
    """Return tracking records when matched to specified document UUID."""

    def _ensure_uuid(item):
        return uuid.UUID(hex=item) if isinstance(item, str) else item

    doc_uuid_list = [_ensure_uuid(item) for item in doc_uuid_list]

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:

        stmt = select(TrackedDocument).where(
            TrackedDocument.id.in_(doc_uuid_list))
        result = session.execute(stmt)
        existing_objs = result.scalars().all()

    # The returned objects are detached from the closed session.
    return existing_objs


def add_or_update_tracking_record(file_dir, file_name, cloud_path, bucket_path):
    """Adds or updates the tracking record for the document.
    """
    create_tables_if_not_existing()

    doc_uuid = generate_uuid_from_name(file_dir+'/'+file_name)

    file_stat = cloud_path.stat()
    size_bytes = file_stat.st_size
    file_modification_time = datetime.fromtimestamp(file_stat.st_mtime)

    # We store the path relative to the bucket. This is useful when we
    # need to move the bucket to another location.
    s3_rel_path = cloud_path.relative_to(bucket_path)

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:
        with session.begin():
            stmt = select(TrackedDocument).where(
                TrackedDocument.id == doc_uuid)
            result = session.execute(stmt)
            existing_obj = result.scalar_one_or_none()

        with session.begin():
            if existing_obj:
                existing_obj.size_bytes = size_bytes
                existing_obj.file_modified_time = file_modification_time
                existing_obj.s3_rel_path = str(s3_rel_path)
            else:
                new_obj = TrackedDocument(
                    id=doc_uuid,
                    status=DocumentStatus.UPLOADED,
                    filedir=file_dir,
                    filename=file_name,
                    size_bytes=size_bytes,
                    file_modified_time=file_modification_time,
                    s3_rel_path=str(s3_rel_path)
                )
                session.add(new_obj)


@contextmanager
def update_tracking_record(doc_uuid):
    """Updates the tracking record for the document.
    """
    if isinstance(doc_uuid, str):
        doc_uuid = uuid.UUID(hex=doc_uuid)

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:

        with session.begin():
            stmt = select(TrackedDocument).where(
                TrackedDocument.id == doc_uuid)
            result = session.execute(stmt)
            existing_obj = result.scalar_one()

        with session.begin():
            yield existing_obj


def delete_tracking_record(doc_uuid):
    """Deletes the tracking record for the document.
    """
    if isinstance(doc_uuid, str):
        doc_uuid = uuid.UUID(hex=doc_uuid)

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:

        with session.begin():
            stmt = delete(TrackedDocument).where(
                TrackedDocument.id == doc_uuid)
            result = session.execute(stmt)
