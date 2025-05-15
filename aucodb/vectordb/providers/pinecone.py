from pinecone.grpc import PineconeGRPC, GRPCClientConfig
from pinecone import ServerlessSpec
from langchain.docstore.document import Document
from langchain_pinecone import PineconeVectorStore
from typing import List, Dict, Any
from .base import VectorDatabase


# Pinecone Vector Database
class PineconeVectorDatabase(VectorDatabase):
    def __init__(
        self,
        embedding_model,
        dimension: int = 384,
        index_name: str = "semantic-search-fast",
        url: str = "http://localhost:5080",
    ):
        self.embedding_model = embedding_model
        self.dimension = dimension
        self.index_name = index_name
        self.vector_store = None

        # Initialize Pinecone client for local instance
        self.pc = PineconeGRPC(api_key="pclocal", host=url)

        # Create index if it doesn't exist
        if not self.pc.has_index(self.index_name):
            self.pc.create_index(
                name=self.index_name,
                vector_type="dense",
                dimension=dimension,
                metric="dotproduct",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                deletion_protection="disabled",
                tags={"environment": "development"},
            )

        # Retrieve index host and initialize vector store
        index_host = self.pc.describe_index(name=self.index_name).host
        index = self.pc.Index(
            host=index_host, grpc_config=GRPCClientConfig(secure=False)
        )
        self.vector_store = PineconeVectorStore(index, self.embedding_model)
        self.index = index

    def store_documents(self, documents: List[Document]) -> None:
        self.vector_store.add_documents(documents)

    def query(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # Embed the query using the embedding model
        query_vector = self.embedding_model.embed_query(query)

        # Perform similarity search on the Pinecone index
        results = self.index.query(
            vector=query_vector, top_k=top_k, include_metadata=True
        )

        # Format results to include text, score, and metadata
        return [
            {"text": match["metadata"].get("text", ""), "score": match["score"]}
            for match in results["matches"]
        ]
