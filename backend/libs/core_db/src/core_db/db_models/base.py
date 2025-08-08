from core_public import OwnerType
from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import DeclarativeBase, registry

DECLARED_METADATA = MetaData()
DECLARED_REGISTRY = registry(metadata=DECLARED_METADATA)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy database models.

    Provides shared metadata and registry for declarative model definitions.
    """

    metadata = DECLARED_METADATA
    registry = DECLARED_REGISTRY


DbOwnerType = ENUM(OwnerType)
