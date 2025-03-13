from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorCollection
from app.database import get_collection, connect_to_mongo, close_mongo_connection
from app.models import Location, LocationCreate, LocationsBatch, PyObjectId
from bson import ObjectId
from typing import List, Optional

app = FastAPI(title="Location Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection

def get_location_collection():
    return get_collection("locations")

@app.post("/locations/", response_model=Location, status_code=status.HTTP_201_CREATED)
async def create_location(location: LocationCreate, 
                         collection: AsyncIOMotorCollection = Depends(get_location_collection)):
    location_dict = location.dict()
    result = await collection.insert_one(location_dict)
    return {**location_dict, "id": result.inserted_id}

@app.post("/locations/batch/", status_code=status.HTTP_201_CREATED)
async def create_locations_batch(batch: LocationsBatch,
                                collection: AsyncIOMotorCollection = Depends(get_location_collection)):
    locations = [loc.dict() for loc in batch.locations]
    result = await collection.insert_many(locations)
    return {"inserted_ids": [str(id) for id in result.inserted_ids]}

@app.get("/locations/", response_model=List[Location])
async def get_locations(limit: Optional[int] = 100,
                       collection: AsyncIOMotorCollection = Depends(get_location_collection)):
    locations = await collection.find().to_list(limit)
    return [Location(**loc, id=loc["_id"]) for loc in locations]

@app.get("/locations/last/", response_model=Location)
async def get_last_location(collection: AsyncIOMotorCollection = Depends(get_location_collection)):
    location = await collection.find_one(sort=[("timestamp", -1)])
    if not location:
        raise HTTPException(status_code=404, detail="No locations found")
    return Location(**location, id=location["_id"])

@app.get("/locations/{location_id}", response_model=Location)
async def get_location(location_id: str,
                      collection: AsyncIOMotorCollection = Depends(get_location_collection)):
    if not ObjectId.is_valid(location_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    location = await collection.find_one({"_id": ObjectId(location_id)})
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return Location(**location, id=location["_id"])

@app.put("/locations/{location_id}", response_model=Location)
async def update_location(location_id: str,
                         updated_location: LocationCreate,
                         collection: AsyncIOMotorCollection = Depends(get_location_collection)):
    if not ObjectId.is_valid(location_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    update_data = updated_location.dict(exclude_unset=True)
    result = await collection.update_one(
        {"_id": ObjectId(location_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location = await collection.find_one({"_id": ObjectId(location_id)})
    return Location(**location, id=location["_id"])

@app.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(location_id: str,
                         collection: AsyncIOMotorCollection = Depends(get_location_collection)):
    if not ObjectId.is_valid(location_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    result = await collection.delete_one({"_id": ObjectId(location_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Location not found")
