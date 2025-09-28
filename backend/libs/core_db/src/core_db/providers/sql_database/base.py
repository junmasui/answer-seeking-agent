import enum


class DataDomain(str, enum.Enum):
    """
    Represent the data domains within the SQL database.

    These domains include, for example, answers, checkpoints, and vectors.
    """

    ANSWERS = 'answers'
    CHECKPOINTS = 'checkpoints'
    VECTORS = 'vectors'
