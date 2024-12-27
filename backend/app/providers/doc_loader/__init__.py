"""
This provides the document loader used by this application.
"""

import os

# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = ['get_doc_loader']

# For now, there is only one document loader provider.
from .unstructured import get_doc_loader
