import pytest
import requests
from aucodb.client import AucoClient
import logging

# Configure logging
logging.basicConfig(
    filename="logs/test_aucoclient.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


@pytest.fixture
def client():
    client = AucoClient(base_url="http://localhost:8000")
    try:
        client.connect()
        logging.info("Set up AucoClient")
        yield client
        client.close()
        logging.info("Tore down AucoClient")
    except ConnectionError:
        pytest.skip("FastAPI server not running at http://localhost:8000")


def test_create_collection(client):
    response = client.create_collection("test_users")
    assert "message" in response
    assert "test_users" in client.list_collections()
    logging.info("Tested creating collection")


def test_add_record(client):
    client.create_collection("test_users")
    record = {"name": "Alice", "age": 30, "email": "alice@example.com"}
    response = client.add("test_users", record)
    assert "record_id" in response
    record_id = response["record_id"]
    fetched_record = client.get("test_users", record_id)
    assert fetched_record["name"] == "Alice"
    logging.info("Tested adding record")


def test_find_records(client):
    client.create_collection("test_users")
    client.add("test_users", {"name": "Alice", "age": 30})
    client.add("test_users", {"name": "Bob", "age": 25})
    client.add("test_users", {"name": "Charlie", "age": 35})
    records = client.find("test_users", "age>=30")
    assert len(records) == 2
    names = [r["name"] for r in records]
    assert "Alice" in names
    assert "Charlie" in names
    logging.info("Tested finding records")


def test_update_record(client):
    client.create_collection("test_users")
    record = {"name": "Alice", "age": 30}
    response = client.add("test_users", record)
    record_id = response["record_id"]
    client.update(
        "test_users", record_id, {"age": "31", "email": "alice.updated@example.com"}
    )
    updated_record = client.get("test_users", record_id)
    assert updated_record["age"] == "31"
    assert updated_record["email"] == "alice.updated@example.com"
    logging.info("Tested updating record")


def test_delete_record(client):
    client.create_collection("test_users")
    record = {"name": "Alice", "age": "30"}
    response = client.add("test_users", record)
    record_id = response["record_id"]
    client.delete("test_users", record_id)
    with pytest.raises(Exception):
        client.get("test_users", record_id)
    logging.info("Tested deleting record")


def test_sort_records(client):
    client.create_collection("test_users")
    client.add("test_users", {"name": "Alice", "age": 30})
    client.add("test_users", {"name": "Bob", "age": 25})
    client.add("test_users", {"name": "Charlie", "age": 35})
    sorted_records = client.sort("test_users", "age", reverse=True)
    ages = [int(r["age"]) for r in sorted_records]
    assert ages == [35, 30, 25]
    logging.info("Tested sorting records")
