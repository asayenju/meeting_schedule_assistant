from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from bson import ObjectId

class User(BaseModel):
    id: Optional[str] = None
    google_id: str
    email: EmailStr
    createdAt: datetime
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class UserCreate(BaseModel):
    google_id: str
    email: EmailStr
    createdAt: datetime = None
    
    def __init__(self, **data):
        if 'createdAt' not in data or data['createdAt'] is None:
            data['createdAt'] = datetime.utcnow()
        super().__init__(**data)