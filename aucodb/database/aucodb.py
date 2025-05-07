import os
import json
from typing import List, Any, Union
import threading
from datetime import datetime
import uuid
import logging
from abc import ABC, abstractmethod
from collections.abc import MutableMapping
from pathlib import Path
import re
import asyncio

os.makedirs("logs", exist_ok=True)
# Configure logging
logging.basicConfig(
    filename="logs/app.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class RecordMeta(ABC):
    @abstractmethod
    def __init__(
        self, created_at: datetime = None, updated_at: datetime = None, **kwargs
    ):
        ...

    @abstractmethod
    def update(self, update_fields: dict):
        ...

    @abstractmethod
    def to_dict(self):
        ...


class JsonBase(MutableMapping):
    def __init__(self, **kwargs):
        self._data = kwargs

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**dict([(k, v) for (k, v) in data.items()]))

    def to_dict(self):
        return dict([(k, v) for (k, v) in self.__dict__.items()])

    def save_dict(self, file_path: str):
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class Record(JsonBase, RecordMeta):
    def __init__(
        self,
        id: str = None,
        created_at: datetime = None,
        updated_at: datetime = None,
        **kargs,
    ):
        super().__init__(**kargs)
        self.id = id or str(uuid.uuid4())
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or self.created_at
        for key, value in kargs.items():
            setattr(self, key, value)

    def update(self, update_fields: dict):
        for key, value in update_fields.items():
            # if getattr(self, key):
            setattr(self, key, value)
            # else:
            # raise ValueError(f"Field {key} does not exist in the Record")
            self.updated_at = datetime.now()

    def __repr__(self):
        content = ", ".join(
            [f"{k}={v}" for (k, v) in self.__dict__.items() if k != "_data"]
        )
        expression = f"Record({content})"
        return expression

    def to_dict(self):
        items = []
        for k, v in self.__dict__.items():
            if k == "_data":
                pass
            elif isinstance(v, Union[str, int, float, bool, list, dict]):
                convert_v = v
                items.append((k, convert_v))
            elif isinstance(v, Record):
                convert_v = v.to_dict()
                items.append((k, convert_v))
            else:
                convert_v = str(v)
                items.append((k, convert_v))
        return dict(items)


class CollectionMeta(ABC):
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def add(self, record: Record):
        pass

    @abstractmethod
    def delete(self, record_id: str):
        pass

    @abstractmethod
    def update(self, record_id: str, updated_dict: dict):
        pass

    @abstractmethod
    def find(self, query: str):
        pass

    @abstractmethod
    def get(self, record_id: str):
        pass

    @abstractmethod
    def sort(self, field: str, reverse: bool = False):
        pass


class Collection(JsonBase, CollectionMeta):
    def __init__(
        self,
        name: str,
        id: str = None,
        records: List[Record] = [],
        lock: threading.Lock = None,
        **kargs,
    ):
        assert name
        super().__init__(**kargs)
        self.name = name
        self.id = id or str(uuid.uuid4())
        self.records = records or []
        self.lock = (
            lock if isinstance(lock, type(threading.Lock())) else threading.Lock()
        )

    def to_dict(self):
        items = []
        for k, v in self.__dict__.items():
            if k == "records":
                convert_v = [rec.to_dict() for rec in v]
                items.append((k, convert_v))
            elif k == "_data":
                pass
            elif isinstance(v, Union[str, int, float, bool, list, dict]):
                items.append((k, v))
            else:
                items.append((k, str(v)))
        return dict(items)

    def save_dict(self, file_path: str):
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)

    @classmethod
    def from_dict(cls, data: dict):
        kv_pairs = []
        for k, v in data.items():
            if k == "records":
                records = [Record.from_dict(v) for v in v]
                kv_pairs.append((k, records))
            else:
                kv_pairs.append((k, v))
        return cls(**dict(kv_pairs))

    def __repr__(self):
        records = [rec.__repr__() for rec in self.records]
        expression = f"Collection(id={self.id}, name={self.name}, records={records}, lock={self.lock})"
        return expression

    def add(self, record: Record):
        if isinstance(record, dict):
            record = Record(**record)
        with self.lock:
            for rec in self.records:
                if rec.id == record.id:
                    raise ValueError("Record with this ID already exists")
            self.records.append(record)
            return "Record added successfully"

    def delete(self, record_id: str):
        with self.lock:
            for record in self.records:
                if record.id == record_id:
                    self.records.remove(record)
                    return "Record deleted successfully"
            raise ValueError("Record not found")

    def update(self, record_id: str, updated_dict: dict):
        with self.lock:
            for i, record in enumerate(self.records):
                if isinstance(record, dict):
                    record = Record(**record)
                if record.id == record_id:
                    record.update(updated_dict)
                    self.records[i] = record
                    return "Record updated successfully"
            raise ValueError("Record not found")

    def find(self, query: str):
        key, operator, value = self.parse_condition_string(query)
        with self.lock:
            if operator == "in":
                filtered_records = [
                    record for record in self.records if getattr(record, key) in value
                ]
                return filtered_records
            if operator == "not in":
                filtered_records = [
                    record
                    for record in self.records
                    if getattr(record, key) not in value
                ]
                return filtered_records
            if operator == ">":
                filtered_records = [
                    record for record in self.records if getattr(record, key) > value
                ]
                return filtered_records
            if operator == ">=":
                filtered_records = [
                    record for record in self.records if getattr(record, key) >= value
                ]
                return filtered_records
            if operator == "<=":
                filtered_records = [
                    record for record in self.records if getattr(record, key) <= value
                ]
                return filtered_records
            if operator == "<":
                filtered_records = [
                    record for record in self.records if getattr(record, key) < value
                ]
                return filtered_records
            if operator == "==":
                filtered_records = [
                    record for record in self.records if getattr(record, key) == value
                ]
                return filtered_records
            if operator == "!=":
                filtered_records = [
                    record for record in self.records if getattr(record, key) != value
                ]
                return filtered_records
            else:
                filtered_records = [
                    record
                    for record in self.records
                    if eval(f"{getattr(record, key)} {operator} {value}")
                ]
                return filtered_records

    def get(self, record_id: str):
        with self.lock:
            for rec in self.records:
                if isinstance(rec, dict):
                    rec = Record(**rec)
                if rec.id == record_id:
                    return rec

    def sort(self, field: str, reverse: bool = False):
        """Sort records by field using merge sort."""

        def merge_sort(arr: List[Record], key: str, reverse: bool):
            if len(arr) <= 1:
                return arr
            mid = len(arr) // 2
            left = merge_sort(arr[:mid], key, reverse)
            right = merge_sort(arr[mid:], key, reverse)
            return merge(left, right, key, reverse)

        def merge(left: List[Record], right: List[Record], key: str, reverse: bool):
            result = []
            i = j = 0
            while i < len(left) and j < len(right):
                left_val = getattr(left[i], key)
                right_val = getattr(right[j], key)

                if left_val is None:
                    result.append(right[j])
                    j += 1
                elif right_val is None:
                    result.append(left[i])
                    i += 1
                else:
                    comparison = (left_val > right_val) - (left_val < right_val)
                    if (comparison <= 0) != reverse:
                        result.append(left[i])
                        i += 1
                    else:
                        result.append(right[j])
                        j += 1
            result.extend(left[i:])
            result.extend(right[j:])
            return result

        with self.lock:
            sorted_docs = merge_sort(self.records.copy(), field, reverse)
            return sorted_docs

    def parse_condition_string(self, condition_str: str):
        """
        Parse a condition string like "age>30" or "city  in  ['London', 'Paris']"
        into a tuple: (key, op, value).
        """
        # Supported operators sorted by descending length to match longer ones first
        operators = ["not in", ">=", "<=", "!=", "==", ">", "<", "in"]

        # Normalize spaces for consistent parsing
        condition_str = condition_str.strip()

        for op in operators:
            # Build regex: use \s* to match optional spaces around operator
            pattern = rf"^(.*?)\s*{re.escape(op)}\s*(.*)$"
            match = re.match(pattern, condition_str)
            if match:
                key, value = match.groups()
                key = key.strip()
                value = value.strip()

                # Try to evaluate value to Python type (e.g., int, list)
                try:
                    value = eval(value)
                except:
                    pass  # Keep as string if eval fails

                return (key, op, value)
        raise ValueError(
            f"Invalid condition format: '{condition_str}. We only support single logical condition x, y with operators: >, <, >=, =<, ==, !, and in'"
        )


class AucoDBMeta(ABC):
    @abstractmethod
    def __init__(
        self, data_name: str, collections: dict[str, Collection], *args, **kwargs
    ):
        pass

    @abstractmethod
    def initialize(self, data_path: str, **kwargs):
        pass

    @abstractmethod
    def add_collection(self, collection: Collection):
        pass

    @abstractmethod
    def save(self):
        pass


from typing import Dict
from pathlib import Path


class AucoDB(AucoDBMeta):
    def __init__(
        self,
        data_name: str = "default",
        data_path: str = "cache/aucodb.json",
        is_overwrite: bool = False,
        collections: List[Collection] = [],
        lock: threading.Lock = None,
        *args,
        **kwargs,
    ):
        self.data_name = data_name
        self.data_path = data_path
        self.is_overwrite = is_overwrite
        self.initialize(data_path)

        if not getattr(self, "collections"):
            self.collections = {}
            if collections:
                for collection in collections:
                    self.add_collection(collection)
        self.lock = threading.Lock()

    def initialize(self, data_path: str, **kwargs):
        """Initialize the database with a JSON file at data_path."""
        self.data_path = Path(data_path)
        os.makedirs(self.data_path.parent, exist_ok=True)
        try:
            if self.data_path.exists() and (not self.is_overwrite):
                with open(self.data_path, "r") as f:
                    data = json.load(f)
                    self.collections = {
                        name: Collection.from_dict(col_data)
                        for name, col_data in data.get("collections", {}).items()
                    }
                    self.data_name = data.get("data_name", "default")
            else:
                self.collections = {}
                # Create an empty JSON file
                self.save()
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON file at {data_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error initializing database: {e}")

    def add_collection(self, collection: Collection):
        """Add a collection to the database."""
        if not isinstance(collection, Collection):
            raise TypeError("Collection must be an instance of Collection")
        self.collections[collection.name] = collection
        self.save()
    
    async def save_async(self):
        async def _call_memory_save(self):
            """Asynchronously save the memory instance"""
            async with self.lock:
                self.memory.save()
        return asyncio.create_task(self._call_memory_save())
    
    def save(self):
        """Save the database to the JSON file."""
        if not self.data_path:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_path, "w") as f:
                json.dump({}, f, indent=4)
        try:
            collections = {
                name: collection.to_dict()
                for name, collection in getattr(self, "collections", {}).items()
            }

            data = {"data_name": self.data_name, "collections": collections}

            with open(self.data_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            raise RuntimeError(f"Error saving database to {self.data_path}: {e}")
