from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from functools import lru_cache

@lru_cache()
def get_bge_m3_embeddings() -> HuggingFaceBgeEmbeddings:
    model_name = "BAAI/bge-m3"
    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": True}
    
    return HuggingFaceBgeEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
