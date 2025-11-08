from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from bson import ObjectId

class AuthToken(BaseModel):
    id: Optional[str] = None
    user_id: str
    encrypted_refresh_token: str
    access_token: str
    access_token_expiry: datetime
    watch_history_id: Optional[str] = None
    updated_at: datetime
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class AuthTokenCreate(BaseModel):
    user_id: str
    encrypted_refresh_token: str
    access_token: str
    access_token_expiry: datetime
    watch_history_id: Optional[str] = None
    updated_at: datetime = None
    
    def __init__(self, **data):
        if 'updated_at' not in data or data['updated_at'] is None:
            data['updated_at'] = datetime.utcnow()
        super().__init__(**data)

class AuthTokenUpdate(BaseModel):
    access_token: Optional[str] = None
    access_token_expiry: Optional[datetime] = None
    watch_history_id: Optional[str] = None
    updated_at: datetime = None
    
    def __init__(self, **data):
        if 'updated_at' not in data:
            data['updated_at'] = datetime.utcnow()
        super().__init__(**data)