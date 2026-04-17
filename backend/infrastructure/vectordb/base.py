from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain_core.documents import Document

class BaseVectorDBAdapter(ABC):
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int = 5, filter: Dict[str, Any] = None) -> List[Document]:
        pass

    @abstractmethod
    def get_retriever(self, k: int = 5):
        pass
