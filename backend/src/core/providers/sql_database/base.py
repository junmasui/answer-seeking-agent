import enum


class DataDomain(str, enum.Enum):
    ANSWERS = 'answers'
    CHECKPOINTS = 'checkpoints'
    VECTORS = 'vectors'
    MIGRATION_BASELINE = 'migration_baseline'

