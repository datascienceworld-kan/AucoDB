import pytest
import tempfile
import os
from pathlib import Path
from aucodb.database import AucoDB, Collection, Record
import logging
from uuid import uuid4

# Configure logging
logging.basicConfig(
    filename="logs/test_aucodb.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


@pytest.fixture
def temp_db():
    # Create a temporary directory for the database file
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_db.json")
        db = AucoDB(data_name="test_db", data_path=db_path)
        logging.info("Set up temporary database")
        yield db
        logging.info("Tore down temporary database")


def test_add_collection(temp_db):
    collection = Collection(name="users")
    temp_db.add_collection(collection)
    temp_db.save()
    assert "users" in temp_db.collections
    assert temp_db.collections["users"].name == "users"
    logging.info("Tested adding collection")


def test_add_record(temp_db):
    collection = Collection(name="users")
    temp_db.add_collection(collection)
    record = Record(name="Alice", age=30, email="alice@example.com")
    temp_db.collections["users"].add(record)
    temp_db.save()
    assert len(temp_db.collections["users"].records) == 1
    assert temp_db.collections["users"].records[0].name == "Alice"
    logging.info("Tested adding record")


def test_add_dict_record(temp_db):
    collection = Collection(name="users")
    temp_db.add_collection(collection)
    record_dict = {
        "id": str(uuid4()),
        "name": "Bob",
        "age": 25,
        "email": "bob@example.com",
    }
    temp_db.collections["users"].add(record_dict)
    temp_db.save()
    assert len(temp_db.collections["users"].records) == 1
    assert temp_db.collections["users"].records[0].name == "Bob"
    logging.info("Tested adding dictionary record")


def test_find_records(temp_db):
    collection = Collection(name="users")
    temp_db.add_collection(collection)
    temp_db.collections["users"].add(Record(name="Alice", age=30))
    temp_db.collections["users"].add(Record(name="Bob", age=25))
    temp_db.collections["users"].add(Record(name="Charlie", age=35))
    found_records = temp_db.collections["users"].find("age>=30")
    assert len(found_records) == 2
    names = [r.name for r in found_records]
    assert "Alice" in names
    assert "Charlie" in names
    logging.info("Tested finding records")


def test_update_record(temp_db):
    collection = Collection(name="users")
    temp_db.add_collection(collection)
    record = Record(name="Alice", age=30)
    temp_db.collections["users"].add(record)
    temp_db.collections["users"].update(
        record.id, {"age": 31, "email": "alice.updated@example.com"}
    )
    updated_record = temp_db.collections["users"].get(record.id)
    assert updated_record.age == 31
    assert updated_record.email == "alice.updated@example.com"
    logging.info("Tested updating record")


def test_delete_record(temp_db):
    collection = Collection(name="users")
    temp_db.add_collection(collection)
    record = Record(name="Alice", age=30)
    temp_db.collections["users"].add(record)
    temp_db.collections["users"].delete(record.id)
    assert len(temp_db.collections["users"].records) == 0
    logging.info("Tested deleting record")


def test_sort_records(temp_db):
    collection = Collection(name="users")
    temp_db.add_collection(collection)
    temp_db.collections["users"].add(Record(name="Alice", age=30))
    temp_db.collections["users"].add(Record(name="Bob", age=25))
    temp_db.collections["users"].add(Record(name="Charlie", age=35))
    sorted_records = temp_db.collections["users"].sort("age", reverse=True)
    ages = [r.age for r in sorted_records]
    assert ages == [35, 30, 25]
    logging.info("Tested sorting records")


def test_save_and_load(temp_db):
    collection = Collection(name="users")
    temp_db.add_collection(collection)
    temp_db.collections["users"].add(Record(name="Alice", age=30))
    temp_db.save()
    new_db = AucoDB(data_path=temp_db.data_path)
    assert "users" in new_db.collections
    assert len(new_db.collections["users"].records) == 1
    assert new_db.collections["users"].records[0]["name"] == "Alice"
    logging.info("Tested saving and loading database")
