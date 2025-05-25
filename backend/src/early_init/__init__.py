"""
This is a very small custom module that
provides early logging configuration and
early environment variables configuration.
"""

from . import config_env, config_logging

# from . import init_debugger

# Explicitly define the exported names: these names are the contract of this module.
__all__ = ['config_env', 'config_logging']
