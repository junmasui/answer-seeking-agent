from core_public import SortDirection
from pydantic.alias_generators import to_snake


def parse_sort_by(str_val):
    """
    Parse a comma-separated string of sort criteria into a list of tuples.

    Each criterion can be prefixed with '-' for descending order or '+' (or no prefix) for ascending
    order. Returns a list of (field_name, direction) tuples where direction is either 'asc' or
    'desc'.
    """

    def _to_sort(x):
        """Parse sort field specification into field name and direction tuple."""
        direction = SortDirection.ASC
        if x.startswith('-'):
            direction = SortDirection.DESC
            x = x[1:]
        x = to_snake(x)
        return (x, direction)

    sort_by = [_to_sort(x) for x in str_val.split(',')]
    return sort_by
