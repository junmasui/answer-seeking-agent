import logging
import uuid

from sqlalchemy import and_, select, update

from core.public_models.prompt import AgentPromptStatus

from ...db_models import DbAgentPrompt
from ...providers.sql_database import DataDomain, get_sessionmaker

logger = logging.getLogger(__name__)


def add_prompt(
    name: str,
    status: AgentPromptStatus,
    system_message: str | None,
    human_message: str | None,
    include_history: bool | None,
    user_id: uuid.UUID = None,
):
    """
    Add a new agent prompt with the specified configuration.

    Creates a new prompt entry with automatic version incrementing. If the status
    is ACTIVE, deactivates all other versions of the same prompt name.
    """
    _add_or_update_agent_prompt(
        name=name,
        status=status,
        system_message=system_message,
        human_message=human_message,
        include_history=include_history,
        user_id=user_id,
    )


def _add_or_update_agent_prompt(
    name: str,
    status: AgentPromptStatus,
    system_message: str | None,
    human_message: str | None,
    include_history: bool | None,
    user_id: uuid.UUID,
):
    """Adds or updates the prompt."""
    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        # We want to know auto-increment the version number.
        # So this query will return the highest version numbered first.
        with session.begin():
            stmt = (
                select(DbAgentPrompt).where(DbAgentPrompt.name == name).limit(1).order_by(DbAgentPrompt.version.desc())
            )
            result = session.execute(stmt)
            existing_obj = result.scalar_one_or_none()

            # IMPORTANT!!
            # We should always access SQLAlchemy object properties inside a transaction. Its ORM
            # has subtle lazy-loading behaviors, including when expire_on_commit=True (which is important
            # for data consistency checking). Doing this will prevent auto-transactions from
            # interferring with the next transaction.
            version = 1 if existing_obj is None else (existing_obj.version + 1)

        with session.begin():
            prompt_uuid = uuid.uuid4()

            new_obj = DbAgentPrompt(
                id=prompt_uuid,
                name=name,
                status=status,
                system_message=system_message,
                human_message=human_message,
                include_history=include_history,
                version=version,
                last_user_id=user_id,
            )
            session.add(new_obj)

        # Only one version can be active
        if status == AgentPromptStatus.ACTIVE and version > 1:
            with session.begin():
                stmt = (
                    update(DbAgentPrompt)
                    .where(and_(DbAgentPrompt.name == name, DbAgentPrompt.version != version))
                    .values(status=AgentPromptStatus.DEACTIVATED)
                )
                result = session.execute(stmt)
