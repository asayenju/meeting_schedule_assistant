from fastapi import APIRouter, WebSocket
from pydantic import BaseModel

router = APIRouter(prefix="/device", tags=["Device"])
class Message(BaseModel):
    message: str

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global connected_esp

    await websocket.accept()
    connected_esp = websocket

    print("ESP32 connected")

    try:
        while True:
            data = await websocket.receive_text()
            print("ESP32 says:", data)
    except:
        print("ESP32 disconnected")
        connected_esp = None


@router.post("/send")
async def send_message(msg: str):
    if connected_esp:
        await connected_esp.send_text(msg)
        return {"status": "message sent"}
    else:
        return {"status": "no esp connected"}
