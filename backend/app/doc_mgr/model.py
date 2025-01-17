import logging
import datetime
import uuid

from sqlalchemy import DateTime, Enum, Integer, MetaData, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.sql.functions import current_timestamp

from ..public_models import DocumentStatus
from ..providers.sql_database import get_engine

logger = logging.getLogger(__name__)

metadata_obj = MetaData()
registry_obj = registry(metadata=metadata_obj)

class Base(DeclarativeBase):
    metadata = metadata_obj
    registry = registry_obj


def create_tables_if_not_existing():
    """Creates tables for model objects defined with this module's `Base`.
    """
    logger.info('creating tables that are absent')
    engine = get_engine()

    metadata_obj.create_all(engine)

def drop_all_tables():
    """Drops all tables for model objects defined with this module's `Base`.
    """
    logger.info('dropping all registered tables')
    engine = get_engine()

    metadata_obj.drop_all(engine)



class TrackedDocument(Base):

    __tablename__ = "tracked_documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), nullable=False)
    filedir: Mapped[str] = mapped_column(String(800), nullable=False)
    filename: Mapped[str] = mapped_column(String(800), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_modified_time: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    s3_rel_path: Mapped[str] = mapped_column(String(800), nullable=False)
    # https://docs.sqlalchemy.org/en/20/orm/extensions/mutable.html
    # and https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#sqlalchemy.dialects.postgresql.ARRAY
    pg_doc_ids: Mapped[list[str]] = mapped_column(MutableList.as_mutable(ARRAY(String)), nullable=True)
    ingested_time: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)

    # Used to track the last user who acted on this document.
    last_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=True)

    # 1. `server_default` means that the value is set inside the "CREATE TABLE" statement
    #    by defining a default value that calls the current_timestamp function.
    # 2. `onupdate` means that the value is set within the "UPDATE" statement.
    #
    # See https://docs.sqlalchemy.org/en/20/core/metadata.html#sqlalchemy.schema.Column.params.server_default
    # and https://docs.sqlalchemy.org/en/20/core/metadata.html#sqlalchemy.schema.Column.params.onupdate
    # and https://docs.sqlalchemy.org/en/20/core/metadata.html#sqlalchemy.schema.Column.params.server_onupdate.
    #
    create_time: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=current_timestamp())
    update_time: Mapped[datetime.datetime] = mapped_column(DateTime, 
        server_default=current_timestamp(), onupdate=current_timestamp(), nullable=True
    )
