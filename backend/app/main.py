# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.calendar import router as calendar_router
from app.api.gmail import router as gmail_router
from app.database import connect_to_mongo, close_mongo_connection
from app.api.device import router as device_router
from contextlib import asynccontextmanager
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    await connect_to_mongo()
    yield
    # Shutdown: Close MongoDB connection
    await close_mongo_connection()

class Data(BaseModel):
    temperature: float
    humidity: float

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # allow all origins (safe for dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router, prefix="/api", tags=["Auth"])
app.include_router(calendar_router, prefix="/api", tags=["Calendar"])
app.include_router(gmail_router, prefix="/api", tags=["Gmail"])
app.include_router(device_router, prefix="/api", tags=["Device"])

@app.get("/")
def root():
    return {
        "message": "Welcome to Google API Demo",
        "routes": ["/api/auth/login", "/api/calendar/freebusy", "/api/gmail/messages", "/api/device"]
    }


@app.post("/send-data")
def receive_data(data: Data):
    print("Received:", data)
    return {"status": "ok", "received": data}
