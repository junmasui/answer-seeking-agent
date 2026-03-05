import logging
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from core_public import PromptStatus
from sqlalchemy import and_, func, select, update
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from core_db.db_models import DbPromptVersion
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def update_prompt_version_record(
    prompt_uuid: uuid.UUID | str, prompt_version_uuid: Optional[uuid.UUID] = None, version: Optional[int] = None
):
    """Updates the prompt version record."""
    if isinstance(prompt_uuid, str):
        prompt_uuid = uuid.UUID(hex=prompt_uuid)

    sessionmaker = get_async_sessionmaker(DataDomain.AGENT)

    async with sessionmaker() as session:
        async with session.begin():
            try:
                stmt = select(DbPromptVersion)
                if prompt_version_uuid is not None:
                    criteria = and_(DbPromptVersion.prompt_id == prompt_uuid, DbPromptVersion.id == prompt_version_uuid)
                if version is not None:
                    criteria = and_(DbPromptVersion.prompt_id == prompt_uuid, DbPromptVersion.version == version)
                stmt = stmt.where(criteria)
                result = await session.execute(stmt)

                existing_obj = result.scalar_one()

            except NoResultFound as ex:
                logger.warning('No tracking doc record found for %s version %s', prompt_uuid, version, exc_info=ex)
                return
            except MultipleResultsFound as ex:
                logger.warning(
                    'Multiple tracking doc records found for %s version %s', prompt_uuid, version, exc_info=ex
                )
                return

            yield existing_obj

            # IMPORTANT!!
            # We should always access SQLAlchemy object properties inside a transaction. Its ORM
            # has subtle lazy-loading behaviors, including when expire_on_commit=True (which is
            # important for data consistency checking). Doing this will prevent auto-transactions
            # from interferring with the next transaction.
            prompt_id = existing_obj.prompt_id
            status = existing_obj.status
            version = existing_obj.version

            # Count versions. The count will be the number of records with this prompt's name.
            stmt = select(func.count()).select_from(DbPromptVersion).where(DbPromptVersion.prompt_id == prompt_id)
            result = await session.execute(stmt)
            version_count = result.scalar()

            # Only one version can be active
            if status == PromptStatus.ACTIVE and version_count > 1:
                stmt = (
                    update(DbPromptVersion)
                    .where(and_(DbPromptVersion.prompt_id == prompt_id, DbPromptVersion.version != version))
                    .value(status=PromptStatus.INACTIVE)
                )
                await session.execute(stmt)
