import logging
import uuid

from sqlalchemy import select

from global_config import get_global_config

from ...db_models import DbTrackedDocumentSet
from ...providers.sql_database import DataDomain, get_sessionmaker

logger = logging.getLogger(__name__)


def add_document_set(name: str, is_new_doc_default: bool, is_public_viewable: bool, user_id: uuid.UUID):
    """
    Add a new document set with the specified configuration.

    Creates a new document set entry in the database with the provided name,
    default status, public visibility, and user ownership information.
    """
    return _add_or_update_document_set(
        name=name, is_new_doc_default=is_new_doc_default, is_public_viewable=is_public_viewable, user_id=user_id
    )


def _add_or_update_document_set(name: str, is_new_doc_default: bool, is_public_viewable: bool, user_id: uuid.UUID):
    """Adds or updates the document set."""
    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        with session.begin():
            stmt = select(DbTrackedDocumentSet).where(DbTrackedDocumentSet.name == name)
            result = session.execute(stmt)
            existing_obj = result.scalar_one_or_none()

        with session.begin():
            if existing_obj:
                doc_set_uuid = existing_obj.id
                existing_obj.name = name
                existing_obj.is_new_doc_default = is_new_doc_default
                existing_obj.is_public_viewable = is_public_viewable
                existing_obj.last_user_id = user_id
            else:
                doc_set_uuid = uuid.uuid4()

                doc_root_dir = get_global_config().doc_manager.doc_root_dir

                rel_path = doc_root_dir + '/' + name

                new_obj = DbTrackedDocumentSet(
                    id=doc_set_uuid,
                    name=name,
                    s3_rel_path=rel_path,
                    is_new_doc_default=is_new_doc_default,
                    is_public_viewable=is_public_viewable,
                    last_user_id=user_id,
                )
                session.add(new_obj)

    return doc_set_uuid
