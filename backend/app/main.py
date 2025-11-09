# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import router as auth_router
from api.calendar import router as calendar_router
from api.gmail import router as gmail_router
from api.gmail_webhook import router as gmail_webhook_router

from database import connect_to_mongo, close_mongo_connection
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    await connect_to_mongo()
    yield
    # Shutdown: Close MongoDB connection
    await close_mongo_connection()

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
app.include_router(gmail_webhook_router, prefix="/api", tags=["Gmail Webhook"])

@app.get("/")
def root():
    return {
        "message": "Welcome to Google API Demo",
        "routes": ["/api/auth/login", "/api/calendar/freebusy", "/api/gmail/messages"]
    }
