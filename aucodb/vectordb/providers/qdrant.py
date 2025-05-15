from langchain.docstore.document import Document
from langchain_community.vectorstores import Qdrant as LangChainQdrant
from typing import List, Dict, Any
from .base import VectorDatabase


# Qdrant Vector Database
class QdrantVectorDatabase(VectorDatabase):
    def __init__(
        self, embedding_model, collection_name: str, url: str = "http://localhost:6333"
    ):
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.url = url
        self.vector_store = None

    def store_documents(self, documents: List[Document]) -> None:
        self.vector_store = LangChainQdrant.from_documents(
            documents,
            self.embedding_model,
            url=self.url,
            collection_name=self.collection_name,
        )

    def query(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        if self.vector_store is None:
            raise ValueError("Vector store not initialized.")
        results = self.vector_store.similarity_search_with_score(query, k=top_k)
        return [{"text": doc.page_content, "score": score} for doc, score in results]
