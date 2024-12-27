import logging
import pprint


pp = pprint.PrettyPrinter(indent=2, width=120, compact=False, underscore_numbers=True, sort_dicts=False)

def dump_logger_tree(logger=None):
    def _dump(_logger):
        node = {
            'name': _logger.name,
            'level': logging.getLevelName(_logger.getEffectiveLevel()),
            'propagate': _logger.propagate,
        }
        if len(_logger.handlers) > 0:
            node['handlers'] =  _logger.handlers,
        if len(_logger.filters) > 0:
            node['filters'] = _logger.filters,
        if len(_logger.getChildren()) > 0:
            node['children'] = [_dump(c) for c in _logger.getChildren()]

        return node

    chain = None
    if logger is None:
        logger = logging.getLogger()
    else:
        chain = [ logger.name ]
        while logger.parent is not None:
            logger = logger.parent
            chain.append(logger.name)

    tree = _dump(logger)

    if chain is not None:
        pp.pprint(chain)
    pp.pprint(tree)
