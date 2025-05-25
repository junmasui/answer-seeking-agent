from functools import cache

from langchain_huggingface import HuggingFaceEmbeddings

from ...signals import start_up_handler

#
# See https://python.langchain.com/docs/integrations/text_embedding/huggingfacehub/
#


@cache
def get_embeddings():
    """
    Return a HuggingFaceEmbeddings instance using the 'sentence-transformers/all-mpnet-base-v2' model.
    This function is cached to ensure only one embeddings model is loaded.
    """
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')

    return embeddings


@start_up_handler
def start(sender):
    """Handle the application startup signal. Currently does nothing."""
    pass
