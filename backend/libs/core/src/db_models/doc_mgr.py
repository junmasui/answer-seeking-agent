import datetime
import logging
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import ARRAY, ENUM
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import current_timestamp

from ..public_models import DocumentStatus
from .base import Base

logger = logging.getLogger(__name__)


class DbTrackedDocumentSet(Base):
    """
    SQLAlchemy model representing a tracked document set in the database.

    Manages collections of documents with properties for default status and public visibility.
    """

    __tablename__ = 'tracked_document_sets'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(800), nullable=False)
    ## status: Mapped[DocumentSetStatus] = mapped_column(Enum(DocumentSetStatus), nullable=False)

    is_new_doc_default: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_public_viewable: Mapped[bool] = mapped_column(Boolean, nullable=False)

    s3_rel_path: Mapped[str] = mapped_column(String(800), nullable=True)

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
    update_time: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=current_timestamp(), onupdate=current_timestamp(), nullable=True
    )

    # Define the relationship to DbTrackedDocument
    documents: Mapped[list['DbTrackedDocument']] = relationship(
        order_by='DbTrackedDocument.id', back_populates='document_set'
    )


DbDocumentStatus = ENUM(DocumentStatus)


class DbTrackedDocument(Base):
    """
    SQLAlchemy model representing a tracked document in the database.

    Stores document metadata, processing status, and relationships to document sets and vector store
    IDs.
    """

    __tablename__ = 'tracked_documents'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    document_set_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey(f'{DbTrackedDocumentSet.__tablename__}.id'))
    status: Mapped[DocumentStatus] = mapped_column(DbDocumentStatus, nullable=False)
    filedir: Mapped[str] = mapped_column(String(800), nullable=False)
    filename: Mapped[str] = mapped_column(String(800), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_modified_time: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    source_url: Mapped[str] = mapped_column(String(800), nullable=False)
    content_type: Mapped[str] = mapped_column(String(800), nullable=False)
    download_time_utc: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)

    s3_rel_path: Mapped[str] = mapped_column(String(800), nullable=False)
    # https://docs.sqlalchemy.org/en/20/orm/extensions/mutable.html
    # and https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#sqlalchemy.dialects.postgresql.ARRAY
    vector_ids: Mapped[list[str]] = mapped_column(MutableList.as_mutable(ARRAY(String)), nullable=True)
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
    update_time: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=current_timestamp(), onupdate=current_timestamp(), nullable=True
    )

    # Define the relationship to TrackedDocumentSet
    document_set: Mapped['DbTrackedDocumentSet'] = relationship(back_populates='documents')
