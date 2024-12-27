"""
This provides the document loader used by this application.
"""

import os
from functools import cache
from pathlib import Path
#import logging

from langchain_unstructured import UnstructuredLoader

from unstructured.chunking import add_chunking_strategy, Chunker
from unstructured.chunking.title import chunk_by_title

from global_config import get_global_config
from ..file_store import get_s3_bucket



# def chunk_by_title(
#     elements: Iterable[Element],
#     *,
#     combine_text_under_n_chars: Optional[int] = None,
#     include_orig_elements: Optional[bool] = None,
#     max_characters: Optional[int] = None,
#     multipage_sections: Optional[bool] = None,
#     new_after_n_chars: Optional[int] = None,
#     overlap: Optional[int] = None,
#     overlap_all: Optional[bool] = None,
# ) -> list[Element]:



#
# Create a document loader.
#
def get_doc_loader(file_path: Path|list[Path]):
    config = get_global_config()

    # When false, process locally and not thru cloud API.
    use_unstructured_cloud_api = config.use_unstructured_cloud_api
    kwargs = {
        'partition_via_api': use_unstructured_cloud_api
    }
    if use_unstructured_cloud_api:
        kwargs['api_key'] = config.unstructured_api_key
    
    loader = UnstructuredLoader(
        file_path = file_path,
        mode='elements',
        strategy='hi_res',
        chunking_strategy='by_title',
        max_characters=2_000,
        combine_text_under_n_chars=200,
        include_orig_elements=True,
        **kwargs
    )

    return loader


