from core_db.db_models import DbPrompt
from core_db.providers.sql_database import DataDomain, get_sessionmaker
from sqlalchemy import func, select


def get_prompt_stats():
    """Return the count of records and maximum updated_date time in the prompt table."""
    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        stmt = select(func.count().label('prompt_count'), func.max(DbPrompt.update_time).label('max_update_time'))
        result = session.execute(stmt).first()
    return {'prompt_count': result[0], 'max_update_time': result[1]}
