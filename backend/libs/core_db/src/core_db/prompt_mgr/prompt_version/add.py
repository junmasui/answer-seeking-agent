import uuid

from core_public.prompt_version import PromptStatus
from sqlalchemy import select

from core_db.db_models import DbPromptVersion
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker


async def add_or_update_prompt_version(
    prompt_id: uuid.UUID,
    status: PromptStatus | None,
    include_history: bool | None,
    system_message: str | None,
    human_message: str | None,
    user_id: uuid.UUID,
):
    """Adds a new prompt version."""
    if status == None:
        status = PromptStatus.ACTIVE

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session:
        # We want to know auto-increment the version number.
        # So this query will return the highest version numbered first.
        async with session.begin():
            stmt = (
                select(DbPromptVersion)
                .where(DbPromptVersion.prompt_id == prompt_id)
                .limit(1)
                .order_by(DbPromptVersion.version.desc())
            )
            result = await session.execute(stmt)
            existing_obj = result.scalar_one_or_none()

            # IMPORTANT!!
            # We should always access SQLAlchemy object properties inside a transaction. Its ORM
            # has subtle lazy-loading behaviors, including when expire_on_commit=True (which is
            # important for data consistency checking). Doing this will prevent auto-transactions
            # from interferring with the next transaction.
            version = 1 if existing_obj is None else (existing_obj.version + 1)

            prompt_version_uuid = uuid.uuid4()

            new_obj = DbPromptVersion(
                id=prompt_version_uuid,
                prompt_id=prompt_id,
                status=status,
                include_history=include_history,
                system_message=system_message,
                human_message=human_message,
                version=version,
                last_user_id=user_id,
            )
            session.add(new_obj)

    return prompt_version_uuid
