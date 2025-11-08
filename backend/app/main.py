# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import router as auth_router
from api.calendar import router as calendar_router
from api.gmail import router as gmail_router

app = FastAPI()

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

@app.get("/")
def root():
    return {
        "message": "Welcome to Google API Demo",
        "routes": ["/api/auth/login", "/api/calendar/freebusy", "/api/gmail/messages"]
    }
