from pydantic.alias_generators import to_snake

from core.public_models import SortDirection


def parse_sort_by(str_val):
    """Parse a comma-separated sort string into a list of field-direction tuples.

    Converts camelCase field names to snake_case and handles direction prefixes.
    Fields prefixed with '-' are sorted in descending order, others in ascending order.
    """
    def _to_sort(x):
        direction = SortDirection.ASC
        if x.startswith('-'):
            direction = SortDirection.DESC
            x = x[1:]
        x = to_snake(x)
        return (x, direction)

    sort_by = [_to_sort(x) for x in str_val.split(',')]
    return sort_by
