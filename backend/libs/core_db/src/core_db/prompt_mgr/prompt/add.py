import uuid

from core_db.db_models import DbPrompt
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker
from core_public import OwnerType
from sqlalchemy import and_, select, update


async def add_or_update_prompt(
    name: str,
    owner_type: OwnerType,
    user_id: uuid.UUID,
):
    """Adds or updates the prompt."""
    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session:
        async with session.begin():
            stmt = select(DbPrompt).where(DbPrompt.name == name)
            result = await session.execute(stmt)
            existing_obj = result.scalar_one_or_none()

        async with session.begin():
            if existing_obj:
                prompt_uuid = existing_obj.id
                existing_obj.name = name
                existing_obj.owner_type = owner_type
                existing_obj.last_user_id = user_id
            else:
                prompt_uuid = uuid.uuid4()

                new_obj = DbPrompt(
                    id=prompt_uuid,
                    name=name,
                    owner_type=owner_type,
                    last_user_id=user_id,
                )
                session.add(new_obj)

    return prompt_uuid