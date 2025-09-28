from core_db.doc_mgr.doc_set.query import get_document_sets

from .add import add_document_set
from .delete import delete_document_set
from .query import list_document_sets
from .stats import get_document_set_statistics
from .update import update_document_set

# Explicitly define the exported names: these names are the contract of this module.
__all__ = [
    'add_document_set',
    'delete_document_set',
    'get_document_sets',
    'list_document_sets',
    'get_document_set_statistics',
    'update_document_set',
]
