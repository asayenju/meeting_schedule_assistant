from fastapi import APIRouter, HTTPException, Request, Response
from app.service.transcribe_service import transcribe_short_audio_sync
from pydantic import BaseModel
import numpy as np
import httpx  # 👈 New library import

# --- External API Configuration ---
EXTERNAL_API_URL = "http://0.0.0.0:8001/get-response"
# ----------------------------------

router = APIRouter(prefix="/audio", tags=["Audio"])

def stereo_to_mono(audio_bytes: bytes) -> bytes:
    """
    Converts 16-bit PCM stereo to mono.
    Assumes little-endian signed 16-bit samples.
    """
    samples = np.frombuffer(audio_bytes, dtype=np.int16)
    if len(samples) % 2 != 0:
        samples = samples[:-1]
    left = samples[0::2]
    right = samples[1::2]
    # Average the samples to create mono
    mono = ((left.astype(np.int32) + right.astype(np.int32)) // 2).astype(np.int16)
    return mono.tobytes()


@router.post("/transcribe")
async def transcribe_audio_stream(request: Request):
    audio_data = await request.body()
    
    if len(audio_data) == 0:
        raise HTTPException(status_code=400, detail="No audio data received.")
        
    print(f"Received {len(audio_data)} bytes of audio.")
    
    try:
        audio_data = stereo_to_mono(audio_data)
        print(f"Converted to mono: {len(audio_data)} bytes. Ready for STT.")
    except Exception as e:
        print(f"Failed to convert audio to mono: {e}")
        # The ESP32 often sends stereo even if configured for mono, so this step is vital.
        raise HTTPException(status_code=500, detail="Audio conversion failed.")

    

    # 2️⃣ Transcribe the audio
    try:
        transcription = transcribe_short_audio_sync(
            audio_content=audio_data,
            sample_rate_hertz=16000
        )
        print(f"Transcription result: {transcription}")
        
        # 3️⃣ Pass transcription to the external API (New Step)
        if transcription:
            print(f"Transcription: {transcription}. Sending to external API...")
            
            # Use httpx for asynchronous request to the external service
            async with httpx.AsyncClient() as client:
                external_response = await client.post(
                    EXTERNAL_API_URL,
                    # Send the transcription as a JSON body
                    json={"input": transcription} 
                )
                external_response.raise_for_status() # Raise exception for 4xx/5xx errors

            # The external API's response (e.g., {"response": "Okay, turning on the light."})
            # is assumed to be JSON, containing the final spoken text.
            response_data = external_response.json()
            response_text = response_data.get("response", "External service provided no response.")
        else:
            response_text = "I did not understand that."

    except httpx.HTTPStatusError as e:
        print(f"External API failed with status {e.response.status_code}")
        response_text = f"External server error: {e.response.status_code}"
    except Exception as e:
        print(f"Transcription or processing failed: {e}")
        response_text = "Sorry, I had an error processing the audio."

    # 4️⃣ Return the final response text to the ESP32
    return Response(content=response_text, media_type="text/plain")

# Define the request body model
class InputText(BaseModel):
    input: str

@router.post("/get-response")
async def get_response(data: InputText):
    """
    Simple API to receive transcription text and return a response.
    """
    user_input = data.input
    print(f"Received transcription: {user_input}")

    # Simple rule-based logic
    if "turn on" in user_input.lower():
        response = "Okay, turning on the light."
    elif "turn off" in user_input.lower():
        response = "Got it, turning off the light."
    else:
        response = f"You said: {user_input}"

    # Return JSON response
    return {"response": response}