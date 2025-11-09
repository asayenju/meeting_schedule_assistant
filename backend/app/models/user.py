from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from bson import ObjectId

class PendingRequest(BaseModel):
    """Model for a pending meeting request email."""
    message_id: str
    thread_id: str
    from_email: str
    subject: str
    body: str
    snippet: Optional[str] = None
    processed_at: datetime
    created_at: datetime

class User(BaseModel):
    id: Optional[str] = None
    google_id: str
    email: EmailStr
    createdAt: datetime
    pending_requests: Optional[List[PendingRequest]] = []  # Array of pending meeting requests
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class UserCreate(BaseModel):
    google_id: str
    email: EmailStr
    createdAt: datetime = None
    pending_requests: Optional[List[PendingRequest]] = []
    
    def __init__(self, **data):
        if 'createdAt' not in data or data['createdAt'] is None:
            data['createdAt'] = datetime.utcnow()
        if 'pending_requests' not in data:
            data['pending_requests'] = []
        super().__init__(**data)