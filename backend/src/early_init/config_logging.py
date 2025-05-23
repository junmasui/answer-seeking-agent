import logging

from rich.console import Console
from rich.logging import RichHandler


class SafeRichHandler(RichHandler):
    def render_message(self, record, message):
        # The RichHandler uses square brackets for its own markup syntax.
        # Thus we need to escape the square brackets that are in the original message.
        if self.markup:
            message = message.replace('[', r'\[').replace(']', r'\]')
        return super().render_message(record, message)


def configure_logging():
    terminal_width = 120
    console = Console(width=terminal_width) if terminal_width else None
    rich_handler = SafeRichHandler(
        show_time=False,
        rich_tracebacks=True,
        tracebacks_code_width=110,
        tracebacks_show_locals=False,
        markup=True,
        show_path=False,
        console=console,
    )
    rich_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(message)s'))

    logger = logging.getLogger('core')
    has_rich_handler = any([isinstance(handler, SafeRichHandler) for handler in logger.handlers])
    if not has_rich_handler:
        logger.addHandler(rich_handler)
        logger.propagate = False
    logger.setLevel(logging.INFO)

    logger2 = logging.getLogger('core_app')
    has_rich_handler = any([isinstance(handler, SafeRichHandler) for handler in logger2.handlers])
    if not has_rich_handler:
        logger2.addHandler(rich_handler)
        logger2.propagate = False
    logger2.setLevel(logging.INFO)

    logger2 = logging.getLogger('core_worker')
    has_rich_handler = any([isinstance(handler, SafeRichHandler) for handler in logger2.handlers])
    if not has_rich_handler:
        logger2.addHandler(rich_handler)
        logger2.propagate = False
    logger2.setLevel(logging.INFO)

    logger = logging.getLogger()
    has_rich_handler = any([isinstance(handler, SafeRichHandler) for handler in logger.handlers])
    if not has_rich_handler:
        logger.addHandler(rich_handler)
    logger.setLevel(logging.INFO)


configure_logging()
