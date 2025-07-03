import logging

from rich.console import Console
from rich.logging import RichHandler
from rich.markup import escape


class SafeRichHandler(RichHandler):
    """
    A custom Rich logging handler that safely escapes square brackets in log messages.

    Extends RichHandler to prevent conflicts between user message content containing square brackets
    and Rich's markup syntax by automatically escaping them.
    """

    def render_message(self, record, message):
        """
        Render the log message, escaping square brackets for Rich markup.

        Overrides RichHandler's render_message to escape square brackets in the original message to
        prevent conflicts with Rich's markup syntax.
        """
        # The RichHandler uses square brackets for its own markup syntax.
        # Thus we need to escape the square brackets that are in the original message.
        if self.markup:
            message = escape(message)
        return super().render_message(record, message)


def configure_logging():
    """
    Configure logging with Rich console handler for better terminal output.

    Sets up a SafeRichHandler for core modules with Rich formatting, tracebacks, and proper console
    width. Prevents duplicate handlers and sets appropriate log levels.
    """
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
    has_rich_handler = any(isinstance(handler, SafeRichHandler) for handler in logger.handlers)
    if not has_rich_handler:
        logger.addHandler(rich_handler)
        logger.propagate = False
    logger.setLevel(logging.INFO)

    logger2 = logging.getLogger('core_app')
    has_rich_handler = any(isinstance(handler, SafeRichHandler) for handler in logger2.handlers)
    if not has_rich_handler:
        logger2.addHandler(rich_handler)
        logger2.propagate = False
    logger2.setLevel(logging.INFO)

    logger2 = logging.getLogger('core_worker')
    has_rich_handler = any(isinstance(handler, SafeRichHandler) for handler in logger2.handlers)
    if not has_rich_handler:
        logger2.addHandler(rich_handler)
        logger2.propagate = False
    logger2.setLevel(logging.INFO)

    logger = logging.getLogger()
    has_rich_handler = any(isinstance(handler, SafeRichHandler) for handler in logger.handlers)
    if not has_rich_handler:
        logger.addHandler(rich_handler)
    logger.setLevel(logging.INFO)

    # Enable SQLAlchemy SQL statement logging
    sa_logger = logging.getLogger('sqlalchemy.engine')
    has_rich_handler = any(isinstance(handler, SafeRichHandler) for handler in sa_logger.handlers)
    if not has_rich_handler:
        sa_logger.addHandler(rich_handler)
        sa_logger.propagate = False
    sa_logger.setLevel(logging.INFO)  # Use DEBUG for SQL + params

    # Enable HTTP request logging for requests (urllib3)
    urllib3_logger = logging.getLogger('urllib3.connectionpool')
    has_rich_handler = any(isinstance(handler, SafeRichHandler) for handler in urllib3_logger.handlers)
    if not has_rich_handler:
        urllib3_logger.addHandler(rich_handler)
        urllib3_logger.propagate = False
    urllib3_logger.setLevel(logging.INFO)

    # Enable HTTP request logging for httpx
    httpx_logger = logging.getLogger('httpx')
    has_rich_handler = any(isinstance(handler, SafeRichHandler) for handler in httpx_logger.handlers)
    if not has_rich_handler:
        httpx_logger.addHandler(rich_handler)
        httpx_logger.propagate = False
    httpx_logger.setLevel(logging.INFO)


configure_logging()
