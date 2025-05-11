from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from jose import JWTError, jwt
import json
import zlib

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://mongo:27017/CAR")
client = MongoClient(MONGODB_URI)
db = client['CAR']
maintenance_collection = db['MAINTENANCE']
users_collection = db['USER']

# JWT settings from auth.py
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-keep-it-secret")
ALGORITHM = "HS256"

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models
class TirePressure(BaseModel):
    frontLeft: int
    frontRight: int
    rearLeft: int
    rearRight: int

class Alert(BaseModel):
    type: str  # 'warning', 'info', 'danger'
    message: str

class MaintenanceRecord(BaseModel):
    service: str
    date: str
    mileage: int

class MaintenanceStatus(BaseModel):
    oilLife: int
    batteryHealth: int
    currentMileage: int
    milesUntilService: int
    engineTemperature: str
    temperatureStatus: str
    tirePressure: TirePressure
    alerts: List[Alert]
    maintenanceHistory: List[MaintenanceRecord]

class MaintenanceUpdate(BaseModel):
    service: str
    mileage: int
    notes: Optional[str] = None

# Router
router = APIRouter()

# Helper function to get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_doc = users_collection.find_one({"email": email})
    if user_doc is None:
        raise credentials_exception
    
    # Decompress user data
    user = json.loads(zlib.decompress(user_doc["data"]).decode('utf-8'))
    return user

@router.get("/status", response_model=MaintenanceStatus)
async def get_maintenance_status(user = Depends(get_current_user)):
    """Get the current maintenance status for the user's vehicle"""
    try:
        # Check if user has maintenance data
        maintenance_data = maintenance_collection.find_one({"email": user["email"]})
        
        if not maintenance_data:
            # If no data exists, create default data
            default_data = {
                "email": user["email"],
                "oilLife": 72,
                "batteryHealth": 95,
                "currentMileage": 45230,
                "milesUntilService": 2000,
                "engineTemperature": "Normal",
                "temperatureStatus": "Operating within normal range",
                "tirePressure": {
                    "frontLeft": 32,
                    "frontRight": 32,
                    "rearLeft": 30,
                    "rearRight": 31
                },
                "alerts": [
                    {
                        "type": "warning",
                        "message": "Tire rotation recommended"
                    },
                    {
                        "type": "info",
                        "message": "Oil change due in 2000 miles"
                    }
                ],
                "maintenanceHistory": [
                    {
                        "service": "Oil Change",
                        "date": "2024-03-15",
                        "mileage": 43000
                    },
                    {
                        "service": "Brake Inspection",
                        "date": "2024-02-28",
                        "mileage": 42500
                    },
                    {
                        "service": "Tire Rotation",
                        "date": "2024-02-01",
                        "mileage": 41800
                    }
                ]
            }
            maintenance_collection.insert_one(default_data)
            return default_data
        
        # Remove MongoDB _id field
        maintenance_data.pop("_id", None)
        return maintenance_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/record")
async def add_maintenance_record(record: MaintenanceUpdate, user = Depends(get_current_user)):
    """Add a new maintenance record"""
    try:
        # Get current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Create new record
        new_record = {
            "service": record.service,
            "date": current_date,
            "mileage": record.mileage
        }
        
        # Update maintenance history
        result = maintenance_collection.update_one(
            {"email": user["email"]},
            {
                "$push": {
                    "maintenanceHistory": {
                        "$each": [new_record],
                        "$position": 0
                    }
                },
                "$set": {
                    "currentMileage": record.mileage
                }
            }
        )
        
        if result.modified_count == 0:
            # If no document was updated, create a new one
            default_data = {
                "email": user["email"],
                "oilLife": 100,
                "batteryHealth": 100,
                "currentMileage": record.mileage,
                "milesUntilService": 5000,
                "engineTemperature": "Normal",
                "temperatureStatus": "Operating within normal range",
                "tirePressure": {
                    "frontLeft": 32,
                    "frontRight": 32,
                    "rearLeft": 32,
                    "rearRight": 32
                },
                "alerts": [],
                "maintenanceHistory": [new_record]
            }
            maintenance_collection.insert_one(default_data)
        
        return {"message": "Maintenance record added successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update")
async def update_maintenance_status(status_update: dict, user = Depends(get_current_user)):
    """Update maintenance status fields"""
    try:
        # Remove any fields that shouldn't be directly updated
        if "email" in status_update:
            del status_update["email"]
        if "maintenanceHistory" in status_update:
            del status_update["maintenanceHistory"]
        
        # Update the maintenance status
        result = maintenance_collection.update_one(
            {"email": user["email"]},
            {"$set": status_update}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="No maintenance data found to update")
        
        return {"message": "Maintenance status updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
