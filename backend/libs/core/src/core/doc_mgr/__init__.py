from core_db.doc_mgr.doc.query import get_documents
from core_db.doc_mgr.doc.update import update_tracking_record
from core_db.doc_mgr.doc_set.query import get_document_sets

from .doc import (
    add_document,
    delete_document,
    get_document_statistics,
    list_documents,
    update_document,
    update_document_status,
)
from .doc_set import (
    add_document_set,
    delete_document_set,
    get_document_set_statistics,
    list_document_sets,
    update_document_set,
)
from .upload import merge_chunked_document, upload_chunk, upload_document

# Explicitly define the exported names: these names are the contract of this module.
__all__ = [
    'add_document',
    'delete_document',
    'get_document_statistics',
    'get_documents',
    'list_documents',
    'update_document',
    'update_document_status',
    'update_tracking_record',
    'add_document_set',
    'delete_document_set',
    'get_document_set_statistics',
    'get_document_sets',
    'list_document_sets',
    'update_document_set',
    'merge_chunked_document',
    'upload_chunk',
    'upload_document',
]
