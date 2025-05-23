from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, registry

DECLARED_METADATA = MetaData()
DECLARED_REGISTRY = registry(metadata=DECLARED_METADATA)


class Base(DeclarativeBase):
    metadata = DECLARED_METADATA
    registry = DECLARED_REGISTRY
