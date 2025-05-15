# from langchain.vectorstores import PGVector
from langchain_community.vectorstores import PGVector
from langchain.docstore.document import Document
from typing import List, Dict, Any
from aucodb.vectordb.providers.base import VectorDatabase


# pgvector Vector Database
class PGVectorDatabase(VectorDatabase):
    def __init__(self, embedding_model, connection_string: str, collection_name: str):
        self.embedding_model = embedding_model
        self.connection_string = connection_string
        self.collection_name = collection_name
        self.vector_store = None

    def store_documents(self, documents: List[Document]) -> None:
        self.vector_store = PGVector.from_documents(
            documents,
            self.embedding_model,
            connection_string=self.connection_string,
            collection_name=self.collection_name,
        )

    def query(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        if self.vector_store is None:
            raise ValueError("Vector store not initialized.")
        results = self.vector_store.similarity_search_with_score(query, k=top_k)
        return [{"text": doc.page_content, "score": score} for doc, score in results]
