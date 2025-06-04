"""This provides the document loader used by this application."""

from pathlib import Path

import nltk
from langchain_unstructured import UnstructuredLoader

from ...lib_config import get_lib_config

from ...signals import start_up_handler


@start_up_handler
def start(sender):
    """
    Download required NLTK data for the unstructured document loader.

    Downloads 'punkt_tab' and 'averaged_perceptron_tagger_eng' to resolve
    compatibility issues between unstructured and NLTK libraries.
    """
    if not sender.is_worker:
        return
    # Some version combinations of unstructured and NLTK throw an error about
    # loading 'punkt_tab'.
    #
    # https://github.com/Unstructured-IO/unstructured/issues/3511
    #
    # Which in turn must respect the solution to:
    # https://github.com/nltk/nltk/issues/3266

    nltk.download('punkt_tab')
    nltk.download('averaged_perceptron_tagger_eng')


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
def get_doc_loader(file_path: Path | list[Path]):
    """
    Return an UnstructuredLoader instance for the given file path(s).
    Configures the loader based on global settings, including whether to use the Unstructured cloud API.
    It uses a 'hi_res' strategy and 'by_title' chunking.
    """
    config = get_lib_config()

    # When false, process locally and not thru cloud API.
    use_unstructured_cloud_api = config.use_unstructured_cloud_api
    kwargs = {'partition_via_api': use_unstructured_cloud_api}
    if use_unstructured_cloud_api:
        kwargs['api_key'] = config.unstructured_api_key

    loader = UnstructuredLoader(
        file_path=file_path,
        mode='elements',
        strategy='hi_res',
        chunking_strategy='by_title',
        max_characters=2_000,
        combine_text_under_n_chars=200,
        include_orig_elements=True,
        **kwargs,
    )

    return loader
