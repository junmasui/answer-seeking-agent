import logging
from datetime import datetime
import uuid
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import select, delete, func, column
from sqlalchemy.orm import aliased, Session, subqueryload

from ..providers.sql_database import get_sessionmaker, get_engine

from .model import metadata_obj, TrackedDocument, TrackedDocumentSet, DocumentStatus


logger = logging.getLogger(__name__)

def generate_uuid_from_name(name):
    # Custom namespace
    namespace = uuid.UUID(hex='a2e3faca15a640a6b3db1021ac43d11e')

    # Generate the UUID from the namespace and name
    return uuid.uuid5(namespace, name)



def create_tables_if_not_existing():
    """Creates tables for model objects defined with this module's `Base`.
    """
    logger.info('creating tables that are absent')
    engine = get_engine()

    metadata_obj.create_all(engine)

    with Session(engine) as session:
        doc_set_count = session.scalar(select(func.count()).select_from(TrackedDocumentSet).limit(10))
        if doc_set_count == 0:
            doc_sets = [
                TrackedDocumentSet(id=uuid.uuid4(), name='default', is_new_doc_default=True, is_public_viewable=True),
                TrackedDocumentSet(id=uuid.uuid4(), name='public 2', is_new_doc_default=False, is_public_viewable=True),
                TrackedDocumentSet(id=uuid.uuid4(), name='public 3', is_new_doc_default=False, is_public_viewable=True),
                TrackedDocumentSet(id=uuid.uuid4(), name='private A', is_new_doc_default=False, is_public_viewable=False),
                TrackedDocumentSet(id=uuid.uuid4(), name='private B', is_new_doc_default=False, is_public_viewable=False)
                ]
            session.add_all(doc_sets)
        session.commit()

def drop_all_tables():
    """Drops all tables for model objects defined with this module's `Base`.
    """
    logger.info('dropping all registered tables')
    engine = get_engine()

    metadata_obj.drop_all(engine)



def list_tracking_document_sets(*, is_default: Optional[bool] = None, is_public: Optional[bool] = None,
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

def add_or_update_document_set(doc_set_uuid, name, is_default, is_pubic, user_id):
    """Adds or updates the document set.
    """

    doc_uuid = generate_uuid_from_name('doc-set:'+name)

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:
        with session.begin():
            stmt = select(TrackedDocumentSet).where(
                TrackedDocumentSet.id == doc_set_uuid)
            result = session.execute(stmt)
            existing_obj = result.scalar_one_or_none()

        with session.begin():
            if existing_obj:
                existing_obj.name = name
                existing_obj.is_new_doc_default = is_default
                existing_obj.is_public_viewable = is_pubic
                existing_obj.last_user_id = user_id
            else:
                new_obj = TrackedDocumentSet(
                    id=doc_uuid,
                    name=name,
                    is_new_doc_default=is_default,
                    is_public_viewable=is_pubic,
                    last_user_id=user_id
                )
                session.add(new_obj)



def list_tracking_records(start: Optional[int] = None, length: Optional[int] = None):
    """Return a page of tracking records.
    
    The implementation is an older known-performance technique. The technique
    creates a CTE (alternatively, a subquery could have been used) where each
    row is augmented with the windowing function ROW_NUMBER. Then the rows whose
    ROW_NUMBER values fall into the page range are choosen. Finally, the row
    data minus the ROW_NUMBER values are returned.
    """
    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:

        paginate = start is not None and length is not None

        core_query = select(TrackedDocument)

        # Apply pagination if requested
        if paginate:
            # When paginating, we add a windowing function to the selected fields.
            cte_query = core_query.add_columns(
                func.row_number().over(order_by=TrackedDocument.filename).label('row_num')
            )
       
            # Create a CTE from the query.
            cte = cte_query.cte(name='row_numbered')

            # Alias the CTE
            WindowedTrackedDocument = aliased(element=TrackedDocument, alias=cte)

            # Query the CTE
            query = select(WindowedTrackedDocument).options(subqueryload(WindowedTrackedDocument.document_set)).where(
                # NOTE: Use the `column` function to directly reference the CTE column
                #   labeled 'row_num'. The reason is that 'row_num' is not a part of
                #   the model.
                # NOTE: ROW_NUMBER is 1-indexed. ROW_NUMBER is also inclusive.
                column('row_num').between(start + 1, start + length)
            )
        else:
            query = core_query.options(subqueryload(TrackedDocument.document_set))

        result = session.execute(query)
        existing_objs = result.scalars().all()

    return existing_objs


def get_tracking_stats():
    """Return the count of records and maximum updated_date time
    in the tracking table.
    """

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:
        stmt = select(
            func.count().label('doc_count'),
            func.max(TrackedDocument.update_time).label('max_update_time')
        )
        result = session.execute(stmt).first()
    return {
        'doc_count': result[0],
        'max_update_time': result[1]
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


def add_or_update_tracking_record(document_set_uuid, file_dir, file_name, cloud_path, bucket_path, user_id):
    """Adds or updates the tracking record for the document.
    """
    if not isinstance(document_set_uuid, uuid.UUID):
        raise TypeError('document_set_uuid must be a UUID object')

    doc_uuid = generate_uuid_from_name('doc:'+file_dir+'/'+file_name)

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
                existing_obj.document_set_id = document_set_uuid
                existing_obj.size_bytes = size_bytes
                existing_obj.file_modified_time = file_modification_time
                existing_obj.s3_rel_path = str(s3_rel_path)
                existing_obj.last_user_id = user_id
            else:
                new_obj = TrackedDocument(
                    id=doc_uuid,
                    document_set_id=document_set_uuid,
                    status=DocumentStatus.UPLOADED,
                    filedir=file_dir,
                    filename=file_name,
                    size_bytes=size_bytes,
                    file_modified_time=file_modification_time,
                    s3_rel_path=str(s3_rel_path),
                    last_user_id=user_id
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
