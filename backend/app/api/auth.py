from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from service.google_service import authenticate_user
from database import get_users_collection, get_auth_tokens_collection
from models.user import UserCreate
from googleapiclient.discovery import build

router = APIRouter(prefix="/google", tags=["Auth"])

@router.get("/auth")
async def authenticate():
    """Authenticate and store OAuth token in MongoDB."""
    try:
        # Authenticate user and get credentials
        google_id, email, creds = await authenticate_user()  # Get email from return
        
        # Create or update user in MongoDB
        users_collection = get_users_collection()
        user_doc = {
            "google_id": google_id,
            "email": email,
            "createdAt": datetime.utcnow(),
            "pending_requests": []
        }
        
        # Upsert user document
        await users_collection.update_one(
            {"google_id": google_id},
            {"$set": user_doc},
            upsert=True
        )
        
        return JSONResponse(content={
            "message": "Authentication successful. Token saved.",
            "google_id": google_id,
            "email": email
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
