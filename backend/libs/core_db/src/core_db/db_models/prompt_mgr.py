import datetime
import logging
import uuid

from core_public import AgentPromptStatus, OwnerType
from sqlalchemy import Boolean, DateTime, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.functions import current_timestamp

from .base import Base, DbOwnerType

logger = logging.getLogger(__name__)

DbPromptStatus = ENUM(AgentPromptStatus)


class DbAgentPrompt(Base):
    """
    SQLAlchemy model representing an agent prompt template in the database.

    Stores versioned prompt templates with system and human messages for AI agent interactions.
    """

    __tablename__ = 'agent_prompt'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[AgentPromptStatus] = mapped_column(DbPromptStatus, nullable=False)
    owner_type: Mapped[OwnerType] = mapped_column(DbOwnerType, nullable=False)

    include_history: Mapped[bool] = mapped_column(Boolean, nullable=True)
    system_message: Mapped[str] = mapped_column(String(9000), nullable=True)
    human_message: Mapped[str] = mapped_column(String(9000), nullable=True)

    # Version number
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Used to track the last user who acted on this prompt.
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
