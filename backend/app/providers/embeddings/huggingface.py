from functools import cache

from langchain_huggingface import HuggingFaceEmbeddings


#
# See https://python.langchain.com/docs/integrations/text_embedding/huggingfacehub/
#

@cache
def get_embeddings():

    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')

    return embeddings
