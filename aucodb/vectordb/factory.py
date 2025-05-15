from typing import Dict, Any
from aucodb.vectordb.providers import ChromaVectorDatabase
from aucodb.vectordb.providers import FAISSVectorDatabase
from aucodb.vectordb.providers import MilvusVectorDatabase
from aucodb.vectordb.providers import PGVectorDatabase
from aucodb.vectordb.providers import PineconeVectorDatabase
from aucodb.vectordb.providers import QdrantVectorDatabase
from aucodb.vectordb.providers import WeaviateVectorDatabase
from aucodb.vectordb.providers.base import VectorDatabase
from aucodb.vectordb.processor.processor import DocumentProcessor
from langchain.docstore.document import Document
from typing import List, Dict, Any, Optional, Union
import yaml
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# Vector Database Factory
class VectorDatabaseFactory:
    SUPPORTED_DBS = {
        "faiss",
        "chroma",
        "milvus",
        "weaviate",
        "qdrant",
        "pinecone",
        "pgvector",
    }

    # Load default configurations from YAML file
    CONFIG_PATH = Path(__file__).parent / "configs.yaml"
    with open(CONFIG_PATH, "r") as config_file:
        DEFAULT_CONFIGS = yaml.safe_load(config_file)

    def __init__(
        self,
        db_type: str,
        embedding_model: Any,
        doc_processor: Optional["DocumentProcessor"] = None,
        db_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the VectorDatabaseFactory.

        Args:
            db_type: Type of vector database
            embedding_model: LangChain embedding model
            doc_processor: Optional document processor
            db_config: Configuration for the vector database, overrides YAML defaults
        """
        self.db_type = db_type.lower()
        self.embedding_model = embedding_model
        self.doc_processor = doc_processor
        self.db_config = db_config or {}
        self._validate_db_type()
        self.vectordb = self._create_vector_database()

    def _validate_db_type(self) -> None:
        """Validate the provided database type."""
        if self.db_type not in self.SUPPORTED_DBS:
            raise ValueError(f"Unsupported vector database type: {self.db_type}")

    def _create_vector_database(self) -> "VectorDatabase":
        """Create a vector database instance based on the specified type."""
        # Merge YAML defaults with user-provided config
        defaults = self.DEFAULT_CONFIGS.get(self.db_type, {})
        config = defaults.copy()  # Avoid modifying the defaults
        config.update(self.db_config)

        try:
            if self.db_type == "faiss":
                return FAISSVectorDatabase(self.embedding_model, config["index_name"])

            elif self.db_type == "chroma":
                return ChromaVectorDatabase(
                    self.embedding_model,
                    config["collection_name"],
                    config["persist_directory"],
                )

            elif self.db_type == "milvus":
                return MilvusVectorDatabase(
                    self.embedding_model,
                    config["collection_name"],
                    config["db_path"],
                    config["metric_type"],
                )

            elif self.db_type == "weaviate":
                return WeaviateVectorDatabase(
                    self.embedding_model, config["class_name"], config["url"]
                )

            elif self.db_type == "qdrant":
                return QdrantVectorDatabase(
                    self.embedding_model, config["collection_name"], config["url"]
                )

            elif self.db_type == "pinecone":
                if not config.get("url"):
                    raise ValueError("URL not provided for Pinecone")
                return PineconeVectorDatabase(
                    self.embedding_model,
                    dimension=config["dimension"],
                    index_name=config["index_name"],
                    url=config["url"],
                )

            elif self.db_type == "pgvector":
                return PGVectorDatabase(
                    self.embedding_model,
                    config["connection_string"],
                    config["collection_name"],
                )

        except KeyError as e:
            raise ValueError(f"Missing required configuration for {self.db_type}: {e}")

    def store_documents(self, list_texts: Union[List[str], List[Document]]) -> None:
        """
        Store documents in the vector database.

        Args:
            list_texts (Union[List[str], List[Document]]) List of documents to store.
        """
        if len(list_texts) > 0 and isinstance(list_texts[0], Document):
            self.vectordb.store_documents(list_texts)
        else:
            documents = self.doc_processor.process_documents(list_texts)
            self.vectordb.store_documents(documents)

    def query(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query the vector database for similar documents.

        Args:
            query (str): Query string.
            top_k (int): Number of top similar documents to retrieve.

        Returns:
            List[Dict[str, Any]]: List of similar documents.
        """
        return self.vectordb.query(query, top_k=top_k)

    # def delete_documents(self, ids: List[str]) -> None:
    #     """
    #     Delete documents from the vector database.

    #     Args:
    #         ids (List[str]): List of document IDs to delete.
    #     """
    #     self.vectordb.delete_documents(ids)

    # def update_document(self, doc_id: str, new_content: str) -> None:
    #     """
    #     Update a document in the vector database.

    #     Args:
    #         doc_id (str): Document ID.
    #         new_content (str): New content for the document.
    #     """
    #     self.vectordb.update_document(doc_id, new_content)
