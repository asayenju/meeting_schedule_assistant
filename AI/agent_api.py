from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from main import generate_response
from backend.app.database import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="Meeting Schedule Assistant API",
    version="1.0.0",
)

class Query(BaseModel):
    input: str
    google_id: str = None  # Optional, will use env var if not provided

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.post("/get-response")
async def get_response_api(query: Query):
    try:
        response_text = generate_response(query.input, google_id=query.google_id)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)