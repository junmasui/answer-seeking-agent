from functools import cache

from langchain_huggingface import HuggingFaceEmbeddings

from ...signals import start_up_handler


#
# See https://python.langchain.com/docs/integrations/text_embedding/huggingfacehub/
#

@cache
def get_embeddings():

    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')

    return embeddings

@start_up_handler
def start(sender):
    pass
