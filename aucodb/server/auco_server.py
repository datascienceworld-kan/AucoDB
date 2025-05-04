import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
from aucodb.database import (
    AucoDB,
    Collection,
    Record,
)  # Assuming aucodb.py contains the provided code
import logging
from pathlib import Path

os.makedirs("logs", exist_ok=True)
# Configure logging
logging.basicConfig(
    filename="auco_server.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="AucoDB Server", version="1.0.0")


# Pydantic models for request/response
class RecordCreate(BaseModel):
    fields: Dict[str, Any]


class RecordUpdate(BaseModel):
    fields: Dict[str, Any]


class CollectionCreate(BaseModel):
    name: str


class QueryRequest(BaseModel):
    query: str


class SortRequest(BaseModel):
    field: str
    reverse: bool = False


@app.on_event("startup")
async def startup_event():
    logging.info("AucoDB Server started")
    # Ensure database is initialized
    db.initialize(db.data_path)


@app.post("/collections/", response_model=dict)
async def create_collection(collection: CollectionCreate):
    try:
        new_collection = Collection(name=collection.name)
        db.add_collection(new_collection)
        db.save()
        return {"message": f"Collection '{collection.name}' created successfully"}
    except Exception as e:
        logging.error(f"Error creating collection: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/collections/", response_model=List[str])
async def list_collections():
    return list(db.collections.keys())


@app.post("/collections/{collection_name}/records/", response_model=dict)
async def add_record(collection_name: str, record: RecordCreate):
    if collection_name not in db.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    try:
        new_record = Record(**record.fields)
        result = db.collections[collection_name].add(new_record)
        db.save()
        return {"message": result, "record_id": new_record.id}
    except Exception as e:
        logging.error(f"Error adding record: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/collections/{collection_name}/records", response_model=dict)
async def get_all_records(collection_name: str):
    if collection_name not in db.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    collection = db.collections[collection_name]
    if not collection:
        raise HTTPException(status_code=404, detail="Collection is empty")
    return collection.to_dict()


@app.get("/collections/{collection_name}/records/{record_id}", response_model=dict)
async def get_record(collection_name: str, record_id: str):
    if collection_name not in db.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    record = db.collections[collection_name].get(str(record_id))
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record.to_dict()


@app.put("/collections/{collection_name}/records/{record_id}", response_model=dict)
async def update_record(collection_name: str, record_id: str, update: RecordUpdate):
    if collection_name not in db.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    try:
        result = db.collections[collection_name].update(record_id, update.fields)
        db.save()
        return {"message": result}
    except Exception as e:
        logging.error(f"Error updating record: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/collections/{collection_name}/records/{record_id}", response_model=dict)
async def delete_record(collection_name: str, record_id: str):
    if collection_name not in db.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    try:
        result = db.collections[collection_name].delete(record_id)
        db.save()
        return {"message": result}
    except Exception as e:
        logging.error(f"Error deleting record: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/collections/{collection_name}/find/", response_model=List[dict])
async def find_records(collection_name: str, query: QueryRequest):
    if collection_name not in db.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    try:
        records = db.collections[collection_name].find(query.query)
        return [record.to_dict() for record in records]
    except Exception as e:
        logging.error(f"Error finding records: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/collections/{collection_name}/sort/", response_model=List[dict])
async def sort_records(collection_name: str, sort: SortRequest):
    if collection_name not in db.collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    try:
        records = db.collections[collection_name].sort(sort.field, sort.reverse)
        return [record.to_dict() for record in records]
    except Exception as e:
        logging.error(f"Error sorting records: {e}")
        raise HTTPException(status_code=400, detail=str(e))


def in_jupyter():
    """Detect if running inside a Jupyter notebook."""
    try:
        from IPython import get_ipython

        return get_ipython() is not None and "IPKernelApp" in get_ipython().config
    except:
        return False


def run(
    host: str = "127.0.0.1",
    port: int = 8000,
    data_path: str = "cache/aucodb.json",
    data_name: str = "aucodb",
):
    # Initialize AucoDB
    global db
    db = AucoDB(data_name="aucodb", data_path="cache/aucodb.json")
    logging.info(f"Initialized AucoDB with name={data_name}, path={data_path}")

    if in_jupyter():
        # Run uvicorn as a server instance in Jupyter
        logging.info("Detected Jupyter environment; starting server via asyncio.")
        import asyncio
        from uvicorn import Config, Server

        config = Config(app=app, host=host, port=port, log_level="debug", reload=True)
        server = Server(config)
        loop = asyncio.get_event_loop()
        loop.create_task(server.serve())
    else:
        logging.info("Starting uvicorn server in terminal mode.")
        uvicorn.run(app, host=host, port=port)
