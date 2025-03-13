from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class LocationBase(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime = datetime.now()

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    id: PyObjectId

    class Config:
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "timestamp": "2023-01-01T12:00:00"
            }
        }

class LocationsBatch(BaseModel):
    locations: List[LocationCreate]
