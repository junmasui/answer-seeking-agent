import enum


class DataDomain(str, enum.Enum):
    """Represents the different data domains within the SQL database, such as answers, checkpoints, and vectors."""

    ANSWERS = 'answers'
    CHECKPOINTS = 'checkpoints'
    VECTORS = 'vectors'
