import logging
import uuid

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..providers.sql_database import get_engine

from .model import metadata_obj, TrackedDocumentSet


logger = logging.getLogger(__name__)

def generate_uuid_from_name():
    
    # Generate random UUID
    return uuid.uuid4()



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


