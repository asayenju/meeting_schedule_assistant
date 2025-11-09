from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from bson import ObjectId

class NegotiationState(BaseModel):
    id: Optional[str] = None
    user_id: str
    thread_id: str
    status: str  # RECEIVED, CHECKING_CALENDAR, SUGGESTED_TIMES, ACCEPTED, REJECTED
    sender_email: EmailStr
    original_request_time: Optional[str] = None
    suggested_times: Optional[List[datetime]] = None
    last_response_sent: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class NegotiationStateCreate(BaseModel):
    user_id: str
    thread_id: str
    status: str
    sender_email: EmailStr
    original_request_time: Optional[str] = None
    suggested_times: Optional[List[datetime]] = None
    last_response_sent: Optional[datetime] = None
    # Remove created_at and updated_at from the model - they're auto-generated
    
    class Config:
        # Exclude these fields from the schema
        json_schema_extra = {
            "example": {
                "user_id": "123456789",
                "thread_id": "thread_abc123",
                "status": "RECEIVED",
                "sender_email": "sender@example.com",
                "original_request_time": "2025-11-08T10:00:00Z"
            }
        }
    
    def __init__(self, **data):
        now = datetime.utcnow()
        # Auto-generate timestamps
        data["created_at"] = now
        data["updated_at"] = now
        super().__init__(**data)

class NegotiationStateUpdate(BaseModel):
    status: Optional[str] = None
    original_request_time: Optional[str] = None
    suggested_times: Optional[List[datetime]] = None
    last_response_sent: Optional[datetime] = None
    updated_at: datetime = None
    
    def __init__(self, **data):
        if 'updated_at' not in data:
            data['updated_at'] = datetime.utcnow()
        super().__init__(**data)