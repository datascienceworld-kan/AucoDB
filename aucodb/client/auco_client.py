import os
import requests
from typing import List, Dict, Any, Optional
import logging
from abc import ABC, abstractmethod

os.makedirs("logs", exist_ok=True)
# Configure logging
logging.basicConfig(
    filename="logs/auco_client.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class AucoClientMeta(ABC):
    @abstractmethod
    def __init__(self, path: str, port: int, *args, **kwargs):
        pass

    @abstractmethod
    def connect(self, base_url: str):
        pass

    @abstractmethod
    def create_collection(self, collection_name: str) -> dict:
        pass

    @abstractmethod
    def list_collections(self) -> List[str]:
        pass

    @abstractmethod
    def add(self, collection_name: str, fields: Dict[str, Any]) -> dict:
        pass

    @abstractmethod
    def get(self, collection_name: str, record_id: str) -> dict:
        pass

    @abstractmethod
    def update(
        self, collection_name: str, record_id: str, fields: Dict[str, Any]
    ) -> dict:
        pass

    @abstractmethod
    def delete(self, collection_name: str, record_id: str) -> dict:
        pass

    @abstractmethod
    def find(self, collection_name: str, query: str) -> List[dict]:
        pass

    @abstractmethod
    def sort(
        self, collection_name: str, field: str, reverse: bool = False
    ) -> List[dict]:
        pass

    @abstractmethod
    def close(self):
        pass


class AucoClient(AucoClientMeta):
    def __init__(
        self, path: str = "cache/aucodb.json", base_url: str = "http://127.0.0.1:8000"
    ):
        self.base_url = base_url
        self.path = path
        self.session = requests.Session()
        logging.info(f"AutoClient initialized with base_url: {base_url}")

    def connect(self, base_url: Optional[str] = None):
        if base_url:
            self.base_url = base_url
        try:
            response = self.session.get(f"{self.base_url}/collections/")
            response.raise_for_status()
            logging.info("Successfully connected to AucoDB server")
            return "Connected to AucoDB server"
        except requests.RequestException as e:
            logging.error(f"Failed to connect to server: {e}")
            raise ConnectionError(f"Cannot connect to {self.base_url}: {e}")

    def create_collection(self, collection_name: str) -> dict:
        try:
            response = self.session.post(
                f"{self.base_url}/collections/", json={"name": collection_name}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error creating collection: {e}")
            raise Exception(f"Failed to create collection: {e}")

    def list_collections(self) -> List[str]:
        try:
            response = self.session.get(f"{self.base_url}/collections/")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error listing collections: {e}")
            raise Exception(f"Failed to list collections: {e}")

    def add(self, collection_name: str, fields: Dict[str, Any]) -> dict:
        try:
            response = self.session.post(
                f"{self.base_url}/collections/{collection_name}/records/",
                json={"fields": fields},
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error adding record: {e}")
            raise Exception(f"Failed to add record: {e}")

    def get(self, collection_name: str, record_id: str = "") -> dict:
        try:
            if record_id:
                response = self.session.get(
                    f"{self.base_url}/collections/{collection_name}/records/{record_id}"
                )
            else:
                response = self.session.get(
                    f"{self.base_url}/collections/{collection_name}/records"
                )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error getting record: {e}")
            raise Exception(f"Failed to get record: {e}")

    def update(
        self, collection_name: str, record_id: str, fields: Dict[str, Any]
    ) -> dict:
        try:
            response = self.session.put(
                f"{self.base_url}/collections/{collection_name}/records/{record_id}",
                json={"fields": fields},
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error updating record: {e}")
            raise Exception(f"Failed to update record: {e}")

    def delete(self, collection_name: str, record_id: str) -> dict:
        try:
            response = self.session.delete(
                f"{self.base_url}/collections/{collection_name}/records/{record_id}"
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error deleting record: {e}")
            raise Exception(f"Failed to delete record: {e}")

    def find(self, collection_name: str, query: str) -> List[dict]:
        try:
            response = self.session.post(
                f"{self.base_url}/collections/{collection_name}/find/",
                json={"query": query},
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error finding records: {e}")
            raise Exception(f"Failed to find records: {e}")

    def sort(
        self, collection_name: str, field: str, reverse: bool = False
    ) -> List[dict]:
        try:
            response = self.session.post(
                f"{self.base_url}/collections/{collection_name}/sort/",
                json={"field": field, "reverse": reverse},
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error sorting records: {e}")
            raise Exception(f"Failed to sort records: {e}")

    def close(self):
        self.session.close()
        logging.info("AutoClient session closed")
