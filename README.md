# AucoDB

AucoDB is a modern, lightweight NoSQL database designed for flexibility, fault tolerance, and seamless integration with agent-based systems. It provides a MongoDB-like document and collection structure, supports JSON-based data storage, and offers both HTTP-based and file-based CRUD operations. With thread-safe I/O and fault-tolerant design, AucoDB ensures data safety and reliability, making it an excellent choice for agent memory and other dynamic applications.

## Features

- **MongoDB-like Document Storage**: Organize data in collections and documents, similar to MongoDB.
- **Flexible JSON Support**: Store any valid JSON class effortlessly.
- **HTTP-based CRUD Operations**: Use `AucoClient` for remote CRUD operations via HTTP.
- **File-based CRUD Operations**: Use `AucoDB` for direct file I/O-based data manipulation.
- **Thread-safe I/O**: Ensure data integrity with thread-safe file operations.
- **Fault Tolerance**: Robust design to handle failures gracefully.
- **Agent Memory Compatibility**: Optimized for use in agent-based systems requiring persistent memory.

## Installation

To get started with AucoDB, clone the repository and install the required dependencies.

### Steps
There are two ways to install AucoDB:

1. Clone the repository:
   ```bash
   git clone https://github.com/datascienceworld-kan/aucodb.git
   cd aucodb
   pip install -r requirements.txt
   poetry install
   ```
2. Install by pip:
   ```
   pip install aucodb==0.1.2
   ```
## Running the AucoDB Server

AucoDB provides a built-in server for HTTP-based operations. The server can be started with a simple Python script.

### Example

```python
from aucodb.server import auco_server

# Run the server on localhost:8000, using a JSON file for storage
auco_server.run(host="127.0.0.1", port=8000, data_path="cache/aucodb.json", data_name="aucodb")
```

This starts the AucoDB server, listening on `http://127.0.0.1:8000` and storing data in `cache/aucodb.json`.

## Using the AucoClient (HTTP-based Operations)

The `AucoClient` allows you to perform CRUD operations on AucoDB collections via HTTP. Below is an example demonstrating how to connect to the server, create collections, and manage records.

### Example

```python
from aucodb.client import AucoClient

# Initialize and connect client
client = AucoClient(base_url='http://localhost:8000')
client.connect()

# Create a collection
message = client.create_collection(collection_name="users")
print(message)

# Add records
user1 = {"name": "Alice", "age": 30, "email": "alice@example.com"}
user2 = {"name": "Bob", "age": 25, "email": "bob@example.com"}
user3 = {"name": "Charlie", "age": 35, "email": "Charlie@example.com"}

user1 = client.add(collection_name="users", fields=user1)
user2 = client.add(collection_name="users", fields=user2)
user3 = client.add(collection_name="users", fields=user3)

# Get a record by ID
record_id = user1["record_id"]
record = client.get(collection_name="users", record_id=record_id)
print(record)

# Find records with condition (age >= 30)
records = client.find(collection_name="users", query="age>=30")
print(records)

# Sort records by age (descending)
sorted_records = client.sort(collection_name="users", field="age", reverse=True)
print(sorted_records)

# Update a record
client.update(collection_name="users", record_id=record_id, fields={"age": 31})
record = client.get(collection_name="users", record_id=record_id)
print(record)

# Delete a record
message = client.delete(collection_name="users", record_id=record_id)
print(message)

# Get all records
records = client.get(collection_name="users")
print(records)

# Close the client
client.close()
```

### Explanation

- **Initialization**: The `AucoClient` connects to the AucoDB server at the specified `base_url`.
- **Collection Management**: Create and manage collections using methods like `create_collection`.
- **CRUD Operations**: Perform create (`add`), read (`get`, `find`), update (`update`), and delete (`delete`) operations.
- **Querying**: Use conditions like `age>=30` for filtering and sorting records.
- **Connection Management**: Always close the client when done to free resources.

## Using AucoDB (File-based Operations)

For direct file-based operations, the `AucoDB` class allows you to manipulate collections and records stored in a JSON file. This is ideal for local applications or when HTTP is not required.

### Example

```python
from aucodb.database import AucoDB, Collection, Record
from datetime import datetime
import logging

# Initialize AucoDB
db = AucoDB(data_name="aucodb", data_path="cache/aucodb.json")

# Create a new collection
users_collection = Collection(name="users")
db.add_collection(collection=users_collection)
logging.info("Created 'users' collection")

# Add records
user1 = {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"}
user2 = {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"}
user3 = {"id": 3, "name": "Charlie", "age": 35, "email": "Charlie@example.com"}

db.collections["users"].add(record=user1)
db.collections["users"].add(record=user2)
db.collections["users"].add(record=user3)
db.save()

# Print all records
print("All users:")
for record in db.collections["users"].records:
    print(record)

# Find records where age >= 30
print("Users with age >= 30:")
found_records = db.collections["users"].find(query="age>=30")
for record in found_records:
    print(record)

# Update a record
db.collections["users"].update(record_id=user1.get("id"), updated_dict={"age": 31, "email": "alice.updated@example.com"})
print("After updating Alice's record:")
updated_record = db.collections["users"].get(record_id=user1.get("id"))
print(updated_record)

# Sort records by age (descending)
print("Users sorted by age (descending):")
sorted_records = db.collections["users"].sort(field="age", reverse=True)
for record in sorted_records:
    print(record)

# Delete a record
db.collections["users"].delete(record_id=user2.get("id"))
print("After deleting Bob's record:")
for record in db.collections["users"].records:
    print(record)

# Demonstrate loading from JSON file
new_db = AucoDB(data_path="cache/aucodb.json")
print("\nLoaded database from JSON:")
for record in new_db.collections["users"].records:
    print(record)
```

### Explanation

- **Initialization**: The `AucoDB` class is initialized with a database name and file path for JSON storage.
- **Collection Management**: Create collections using the `Collection` class and add them to the database.
- **CRUD Operations**: Add, retrieve, update, and delete records directly in the JSON file.
- **Persistence**: Use `db.save()` to persist changes to the JSON file.
- **Querying**: Filter and sort records using methods like `find` and `sort`.
- **File Loading**: Load an existing database from a JSON file for continued operations.

## Fault Tolerance and Thread Safety

AucoDB is designed with fault tolerance and thread-safe I/O operations to ensure data integrity. The database handles failures gracefully and prevents data corruption during concurrent operations, making it reliable for multi-threaded applications.

## Use Cases

- **Agent Memory**: Store and retrieve agent state and memory efficiently.
- **Prototyping**: Rapidly develop applications with flexible JSON-based storage.
- **Local Applications**: Use file-based operations for standalone applications.
- **Distributed Systems**: Leverage HTTP-based operations for remote data access.

## Contributing

Contributions to AucoDB are welcome! Please submit issues and pull requests via the [GitHub repository](https://github.com/datascienceworld-kan/AucoDB). Ensure your code follows the project's coding standards and includes appropriate tests.

## License

AucoDB is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
