from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from service.google_service import get_google_services

router = APIRouter(prefix="/google", tags=["Auth"])

@router.get("/auth")
def authenticate():
    """Authenticate and store OAuth token."""
    try:
        get_google_services()
        return {"message": "Authentication successful. Token saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


