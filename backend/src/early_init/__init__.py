"""
This is a very small custom module that
provides early logging configuration and
early environment variables configuration.
"""

from .config_env import configure_env
from .config_logging import configure_logging

#configure_env(base_env='backend.env', overrides_env='backend.overrides.env')
configure_logging()

from . import init_debugger 
