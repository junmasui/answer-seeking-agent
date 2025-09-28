import logging
import uuid

from core_db.doc_mgr.doc_set.add import add_or_update_document_set

logger = logging.getLogger(__name__)


def add_document_set(name: str, is_new_doc_default: bool, is_public_viewable: bool, user_id: uuid.UUID):
    """
    Add a new document set with the specified configuration.

    Creates a new document set entry in the database with the provided name, default status, public
    visibility, and user ownership information.
    """
    return add_or_update_document_set(
        name=name, is_new_doc_default=is_new_doc_default, is_public_viewable=is_public_viewable, user_id=user_id
    )
