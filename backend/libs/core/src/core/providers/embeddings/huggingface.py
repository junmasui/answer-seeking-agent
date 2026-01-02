from functools import cache

from langchain_huggingface import HuggingFaceEmbeddings

from ...signals import start_up_handler

#
# See https://python.langchain.com/docs/integrations/text_embedding/huggingfacehub/
#


@cache
def get_embeddings():
    """
    Return a cached HuggingFaceEmbeddings instance.

    This function, which is cached to ensure a single instance, returns a HuggingFaceEmbeddings
    instance that uses the 'sentence-transformers/all-mpnet-base-v2' model.
    """
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')

    return embeddings


@start_up_handler
async def start(_sender):
    """
    Handle the application startup signal.

    Currently does nothing.
    """
    pass
