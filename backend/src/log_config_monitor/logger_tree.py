import logging
import logging.handlers
import pprint


pp = pprint.PrettyPrinter(
    indent=2, width=120, compact=False, underscore_numbers=True, sort_dicts=False)


def dump_logger_tree(logger=None, include_all=False):
    """Returns the logger hierarchy.

    Knowledge of the actual logger hierarchy in the running process
    is very helpful.

    While python's standard logging framework is powerful, there is often some questions
    about the actual logger hierarchy. The actual logger hierarchy is needed for
    properly targetting and setting logging levels.
    """
    def _dump_handler(_handler: logging.Handler):
        node = {
            'name': _handler.get_name(),
            'type': type(_handler).__qualname__,
            'level': logging.getLevelName(_handler.level),
        }
        if getattr(_handler, 'formatter', None):
            node['formatter'] = _handler.formatter,

        return node

    def _dump_logger(_logger, include_all=include_all):
        node = {
            'name': _logger.name,
            'level': logging.getLevelName(_logger.getEffectiveLevel()),
            'propagate': _logger.propagate,
        }
        if include_all:
            if len(_logger.filters) > 0:
                node['filters'] = _logger.filters,
            if len(_logger.handlers) > 0:
                node['handlers'] = [_dump_handler(h) for h in _logger.handlers],
        if len(_logger.getChildren()) > 0:
            node['children'] = [_dump_logger(c) for c in _logger.getChildren()]

        return node

    if logger is None:
        logger = logging.getLogger()

    tree = _dump_logger(logger)

    return tree
