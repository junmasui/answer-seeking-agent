import logging
from rich.console import Console
from rich.logging import RichHandler

def configure_logging():

    terminal_width = 120
    console = Console(width=terminal_width) if terminal_width else None
    rich_handler = RichHandler(
        show_time=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True,
        show_path=False,
        console=console,
    )
    rich_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(message)s'))

    logger = logging.getLogger('demo-app')
    has_rich_handler = any([isinstance(handler, RichHandler) for handler in logger.handlers])
    if not has_rich_handler:
        logger.addHandler(rich_handler)
        logger.propagate = False
    logger.setLevel(logging.INFO)

    logger2 = logging.getLogger('logic')
    has_rich_handler = any([isinstance(handler, RichHandler) for handler in logger2.handlers])
    if not has_rich_handler:
        logger2.addHandler(rich_handler)
        logger2.propagate = False
    logger2.setLevel(logging.INFO)

    logger2 = logging.getLogger('worker')
    has_rich_handler = any([isinstance(handler, RichHandler) for handler in logger2.handlers])
    if not has_rich_handler:
        logger2.addHandler(rich_handler)
        logger2.propagate = False
    logger2.setLevel(logging.INFO)

    logger = logging.getLogger()
    has_rich_handler = any([isinstance(handler, RichHandler) for handler in logger.handlers])
    if not has_rich_handler:
        logger.addHandler(rich_handler)
    logger.setLevel(logging.INFO)
