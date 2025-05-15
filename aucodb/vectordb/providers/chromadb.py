from langchain.docstore.document import Document
from typing import List, Dict, Any

# from langchain.vectorstores import Chroma
from langchain_community.vectorstores import Chroma
from .base import VectorDatabase


# Chroma Vector Database
class ChromaVectorDatabase(VectorDatabase):
    def __init__(self, embedding_model, collection_name: str, persist_directory: str):
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.vector_store = None

    def store_documents(self, documents: List[Document]) -> None:
        self.vector_store = Chroma.from_documents(
            documents,
            self.embedding_model,
            collection_name=self.collection_name,
            persist_directory=self.persist_directory,
        )

    def query(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        if self.vector_store is None:
            raise ValueError("Vector store not initialized.")
        results = self.vector_store.similarity_search_with_score(query, k=top_k)
        return [{"text": doc.page_content, "score": score} for doc, score in results]
