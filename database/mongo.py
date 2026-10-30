import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017"
)

MONGO_DB = os.getenv(
    "MONGO_DB",
    "local_page_agent"
)

client = MongoClient(MONGO_URI)

db = client[MONGO_DB]

local_pages_collection = db["local_pages"]


def save_local_page(data: dict):
    result = local_pages_collection.insert_one(data)

    return str(result.inserted_id)


def get_local_page(page_id):
    from bson import ObjectId

    try:
        document = local_pages_collection.find_one(
            {"_id": ObjectId(page_id)}
        )

        if document:
            document["_id"] = str(document["_id"])

        return document

    except Exception:
        return None
    

contact_messages_collection = db["contact_messages"]


def save_contact_message(data: dict):
    result = contact_messages_collection.insert_one(data)
    return str(result.inserted_id)    