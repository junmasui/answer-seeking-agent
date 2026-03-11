from sqlalchemy import func, select

from core_db.db_models import DbPromptVersion
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker


async def get_prompt_version_stats():
    """Return the count of records and maximum updated_date time in the prompt version table."""
    sessionmaker = get_async_sessionmaker(DataDomain.AGENT)

    async with sessionmaker() as session:
        stmt = select(
            func.count().label('prompt_version_count'), func.max(DbPromptVersion.update_time).label('max_update_time')
        )
        result = await session.execute(stmt)
        result = result.first()
    return {'prompt_version_count': result[0], 'max_update_time': result[1]}
