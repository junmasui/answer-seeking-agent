import logging
import logging.config
import tomllib
from functools import cache
from pathlib import Path

from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from global_config import get_global_config

logger = logging.getLogger(__name__)


def _apply_incremental_configuration(log_config_path):
    """Apply incremental configuration from the specified TOML file.
    """
    # Read the logging config file
    with log_config_path.open('rb') as fin:
        config = tomllib.load(fin)

    if not isinstance(config, dict):
        return

    if logger.getEffectiveLevel() <= logging.DEBUG:
        import pprint
        formatted = pprint.pformat(object=config, width=120, indent=2, sort_dicts=True)
        logger.debug('Incremental logging config to be applied:\n%s', formatted)

    # Incremental configuration change will affect only `level` in handlers, loggers and root
    # and `propagate` in loggers and root.
    #
    # See https://docs.python.org/3/library/logging.config.html#incremental-configuration
    #
    # Also, the configuration dictionary must contain a `"version"` key with value `1`.
    # This is mandatory for future backward compatibility. We hard-code it here. In the
    # future, we will push the `"version"` to the TOML file.
    config.update({
        'version': 1,
        'incremental': True}
    )

    try:
        logging.config.dictConfig(config)
    except Exception as ex:
        logger.warning(
            'Error during incremental logging reconfiguration', exc_info=ex)

    logger.info('Updated logging levels')


class _ConfigFileChangeEventHandler(PatternMatchingEventHandler):
    """Watches for changes to logging configuration TOML file.
    """

    def _handle(self, event: FileSystemEvent, use_target_path: bool = False) -> None:

        log_config_path = get_global_config().logging_config_path

        # Exit if the logging config file does not exist.
        if not log_config_path.exists():
            return

        # Move FileSystemEvents will put the new name into the event's target_path property.
        event_file_path = event.target_path if use_target_path else event.src_path
        event_file_path = Path(event_file_path)

        # Exit if the event did not target the logging config file.
        if not log_config_path.samefile(event_file_path):
            return

        _apply_incremental_configuration(log_config_path)

    def on_created(self, event: FileSystemEvent) -> None:
        self._handle(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._handle(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        self._handle(event)


class LogConfigMonitor:
    observer = None

    def start(self):
        if self.observer is not None:
            return

        log_config_path = get_global_config().logging_config_path

        # Beware! Watchdog's PatternMatchingEventHandler's patterns is a collection of
        # strings. So be sure to cast the Path object to string object.
        event_handler = _ConfigFileChangeEventHandler(
            patterns=[str(log_config_path)])

        self.observer = Observer()
        self.observer.schedule(event_handler, '.', recursive=False)
        self.observer.start()

        # Let's just apply incremental logging configuration so that we
        # know that we haven't missed a change in the window between the
        # full configuration occurring and this point.
        _apply_incremental_configuration(log_config_path)

    def stop(self):
        self.observer.stop()
        self.observer.join()
        self.observer = None


@cache
def get_logging_conf_monitor():
    return LogConfigMonitor()
