from typing import List, Dict, Any
from abc import ABC, abstractmethod
from langchain.schema import Document


# Abstract Vector Database Interface
class VectorDatabase(ABC):
    @abstractmethod
    def store_documents(self, documents: List[Document]) -> None:
        pass

    # @abstractmethod
    # def delete_documents(self, ids: List[str]) -> None:
    #     pass

    # @abstractmethod
    # def update_document(self, doc_id: str, new_content: str) -> None:
    #     pass

    @abstractmethod
    def query(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        pass
