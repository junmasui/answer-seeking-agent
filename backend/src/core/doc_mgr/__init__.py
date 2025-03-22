# Importing event_handlers will register its start-up event handler.
from . import event_handlers

from .doc import (
    get_documents, list_documents,
    get_document_statistics,
    add_document,
    delete_document,
    update_document, update_document_status, update_tracking_record
)

from .doc_set import (
    get_document_sets, list_document_sets,
    get_document_set_statistics,
    add_document_set,
    delete_document_set,
    update_document_set
)

from .upload import (upload_chunk, upload_document, merge_chunked_document)