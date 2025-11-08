# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import router as auth_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # allow all origins (safe for dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router, prefix="/api", tags=["Auth"])

@app.get("/")
def root():
    return {
        "message": "Welcome to Google API Demo",
        "routes": ["/api/auth/login", "/api/calendar/freebusy", "/api/gmail/messages"]
    }
