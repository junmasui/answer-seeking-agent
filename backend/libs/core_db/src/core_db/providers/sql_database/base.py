import enum


class DataDomain(str, enum.Enum):
    """
    Represent the data domains within the SQL database.

    These domains include, for example, agent, checkpoints, and vectors.
    """

    AGENT = 'agent'
    CHECKPOINTS = 'checkpoints'
    VECTORS = 'vectors'
