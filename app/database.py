import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "location_tracker"

client = None
database = None

async def connect_to_mongo():
    global client, database
    client = AsyncIOMotorClient(MONGO_URI)
    database = client[DB_NAME]

async def close_mongo_connection():
    client.close()

def get_collection(collection_name: str):
    return database[collection_name]
