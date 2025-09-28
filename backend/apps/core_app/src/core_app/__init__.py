import early_init as _early_init  # noqa: I001, F401 ## loading this module configures environment and logging

from .main import app

# Explicitly define the exported names: these names are the contract of this module.
__all__ = ['app']
