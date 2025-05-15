from aucodb.vectordb.providers.base import VectorDatabase
from pymilvus import MilvusClient
from langchain.docstore.document import Document
from typing import List, Dict, Any


# Milvus Lite Vector Database
class MilvusVectorDatabase(VectorDatabase):
    def __init__(
        self,
        embedding_model,
        collection_name: str,
        db_path: str = "./milvus_lite.db",
        metric_type: str = "COSINE",
        dimension: int = 384,
    ):
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.db_path = db_path
        self.metric_type = metric_type.upper()  # Ensure uppercase (COSINE, L2, etc.)
        self.client = MilvusClient(self.db_path)
        self.dimension = (
            dimension  # Assuming embedding model produces 384-dimensional vectors
        )
        self.vector_store = None

    def store_documents(self, documents: List[Document]) -> None:
        # Create or recreate collection
        if self.client.has_collection(self.collection_name):
            self.client.drop_collection(self.collection_name)

        self.client.create_collection(
            collection_name=self.collection_name,
            dimension=self.dimension,
            metric_type=self.metric_type,  # Explicitly set metric type
        )

        # Generate embeddings for documents
        texts = [doc.page_content for doc in documents]
        vectors = self.embedding_model.embed_documents(texts)

        # Prepare data for insertion
        data = [
            {"id": i, "vector": vectors[i], "text": texts[i]}
            for i in range(len(documents))
        ]

        # Insert data into Milvus Lite
        self.client.insert(collection_name=self.collection_name, data=data)
        self.vector_store = True  # Indicate store is initialized

    def query(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Store documents first.")

        # Generate embedding for query
        query_vector = self.embedding_model.embed_query(query)

        # Perform similarity search
        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            limit=top_k,
            output_fields=["text"],
            search_params={
                "metric_type": self.metric_type
            },  # Use consistent metric type
        )

        # Format results
        formatted_results = []
        for result in results[0]:  # results[0] contains hits for the first query vector
            formatted_results.append(
                {
                    "text": result["entity"]["text"],
                    "score": result[
                        "distance"
                    ],  # COSINE: higher is better; L2: lower is better
                }
            )

        return formatted_results
