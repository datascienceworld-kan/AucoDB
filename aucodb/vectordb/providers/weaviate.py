from typing import List, Dict, Any
from langchain.docstore.document import Document
from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.classes.config import Configure, Property, DataType
from urllib.parse import urlparse
from .base import VectorDatabase


# Weaviate Vector Database
class WeaviateVectorDatabase(VectorDatabase):
    def __init__(
        self, embedding_model, class_name: str, url: str = "http://localhost:8080"
    ):
        """
        Initialize Weaviate vector database.

        Args:
            embedding_model: LangChain embedding model.
            class_name: Name of the Weaviate collection to redact class_name
            url: URL of the Weaviate server.
        """
        self.embedding_model = embedding_model
        self.class_name = class_name
        self.url = url
        self.client = None
        self._initialize_client()
        self._setup_collection()

    def _initialize_client(self):
        """Initialize Weaviate client with connection parameters."""
        parsed_url = urlparse(self.url)
        host = parsed_url.hostname
        port = parsed_url.port if parsed_url.port else 80
        protocol = parsed_url.scheme

        connection_params = ConnectionParams.from_params(
            http_host=host,
            http_port=port,
            http_secure=protocol == "https",
            grpc_host=host,
            grpc_port=50051,
            grpc_secure=protocol == "https",
        )

        self.client = WeaviateClient(
            connection_params=connection_params,
            additional_config=AdditionalConfig(
                timeout=Timeout(init=30, query=60, insert=120)
            ),
            skip_init_checks=False,
        )
        self.client.connect()

    def _setup_collection(self):
        """Set up the Weaviate collection schema if it doesn't exist."""
        if not self.client.collections.exists(self.class_name):
            self.client.collections.create(
                name=self.class_name,
                properties=[Property(name="text", data_type=DataType.TEXT)],
                vectorizer_config=Configure.Vectorizer.none(),
            )

    def store_documents(self, documents: List[Document]) -> None:
        """Store documents in Weaviate collection."""
        collection = self.client.collections.get(self.class_name)
        try:
            with collection.batch.dynamic() as batch:
                for doc in documents:
                    vector = self.embedding_model.embed_documents([doc.page_content])[0]
                    batch.add_object(
                        properties={"text": doc.page_content}, vector=vector
                    )
        except Exception as e:
            raise Exception(f"Error adding documents: {e}")

    def query(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform a semantic search on the collection."""
        collection = self.client.collections.get(self.class_name)
        query_vector = self.embedding_model.embed_documents([query])[0]
        try:
            response = collection.query.near_vector(
                near_vector=query_vector, limit=top_k, return_properties=["text"]
            )
            return [
                {"text": obj.properties["text"], "score": obj.metadata.distance}
                for obj in response.objects
            ]
        except Exception as e:
            raise Exception(f"Error querying: {e}")

    def __del__(self):
        """Close the client connection when the object is destroyed."""
        if self.client:
            self.client.close()
