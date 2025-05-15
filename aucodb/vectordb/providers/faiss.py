from langchain.docstore.document import Document

# from langchain.vectorstores import FAISS
from langchain_community.vectorstores import FAISS
from typing import List, Dict, Any
from .base import VectorDatabase


# FAISS Vector Database
class FAISSVectorDatabase(VectorDatabase):
    def __init__(self, embedding_model, index_name: str):
        self.embedding_model = embedding_model
        self.index_name = index_name
        self.vector_store = None

    def store_documents(self, documents: List[Document]) -> None:
        self.vector_store = FAISS.from_documents(documents, self.embedding_model)

    def query(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        if self.vector_store is None:
            raise ValueError("Vector store not initialized.")
        results = self.vector_store.similarity_search_with_score(query, k=top_k)
        return [{"text": doc.page_content, "score": score} for doc, score in results]
