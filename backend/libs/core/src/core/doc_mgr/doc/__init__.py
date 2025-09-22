from core_db.doc_mgr.doc.query import get_documents
from core_db.doc_mgr.doc.update import update_tracking_record
from .add import add_document
from .delete import delete_document
from .query import list_documents
from .stats import get_document_statistics
from .update import update_document, update_document_status

# Explicitly define the exported names: these names are the contract of this module.
__all__ = [
    'add_document',
    'delete_document',
    'get_documents',
    'list_documents',
    'get_document_statistics',
    'update_document',
    'update_document_status',
    'update_tracking_record',
]
