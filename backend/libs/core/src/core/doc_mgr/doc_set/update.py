import logging

from core_db.doc_mgr.doc_set.update import update_doc_set_record

from ...lib_config import get_lib_config

logger = logging.getLogger(__name__)


def update_document_set(doc_set_uuid, name=None, is_new_doc_default=None, is_public_viewable=None, last_user_id=None):
    """
    Update specific fields of a document set record.

    Updates the document set with the provided field values. Only non-None parameters will be
    updated in the database record.
    """
    with update_doc_set_record(doc_set_uuid=doc_set_uuid) as record:
        if name is not None and record.name != name:
            doc_root_dir = get_lib_config().doc_root_dir
            s3_rel_path = doc_root_dir + '/' + name

            record.name = name
            record.s3_rel_path = s3_rel_path

        if is_new_doc_default is not None:
            record.is_new_doc_default = is_new_doc_default

        if is_public_viewable is not None:
            record.is_public_viewable = is_public_viewable

        if last_user_id:
            record.last_user_id = last_user_id
