from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from infrastructure.vectordb.base import BaseVectorDBAdapter
from infrastructure.embeddings.bge_m3 import get_bge_m3_embeddings
from config.settings import get_settings

class QdrantAdapter(BaseVectorDBAdapter):
    def __init__(self, collection_name: str = "agronomy_docs"):
        self.settings = get_settings()
        self.collection_name = collection_name
        self.embeddings = get_bge_m3_embeddings()
        
        # Ambiente de desenvolvimento usa persistência local (memory/disk) sem precisar do Docker.
        if self.settings.ENVIRONMENT == "development":
            self.client = QdrantClient(location=":memory:")
        else:
            self.client = QdrantClient(
                url=f"http://{self.settings.QDRANT_HOST}:{self.settings.QDRANT_PORT}",
                api_key=self.settings.QDRANT_API_KEY
            )
            
        self._ensure_collection()
            
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )

    def _ensure_collection(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )

    def add_documents(self, documents: List[Document]) -> List[str]:
        return self.vector_store.add_documents(documents)

    def similarity_search(self, query: str, k: int = 5, filter: dict = None) -> List[Document]:
        return self.vector_store.similarity_search(query, k=k, filter=filter)

    def get_retriever(self, k: int = 5):
        return self.vector_store.as_retriever(search_kwargs={"k": k})
