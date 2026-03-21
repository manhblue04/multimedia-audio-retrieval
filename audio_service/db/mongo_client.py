import os
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "audio_retrieval")
COLLECTION_NAME = "audio_features"

_client: MongoClient = None


def get_collection() -> Collection:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = _client[DB_NAME]
    col = db[COLLECTION_NAME]
    col.create_index([("instrument", ASCENDING)], background=True)
    return col


def insert_document(doc: dict):
    col = get_collection()
    existing = col.find_one({"file_name": doc["file_name"]})
    if existing:
        col.replace_one({"file_name": doc["file_name"]}, doc)
    else:
        col.insert_one(doc)


def get_all_documents() -> list:
    col = get_collection()
    return list(col.find({}, {"_id": 0}))


def get_count() -> int:
    return get_collection().count_documents({})


def get_instruments() -> list:
    return get_collection().distinct("instrument")
