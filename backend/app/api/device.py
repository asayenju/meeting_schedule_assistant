from fastapi import APIRouter, HTTPException, Request, Response
from app.service.transcribe_service import transcribe_short_audio_sync
import numpy as np

router = APIRouter(prefix="/audio", tags=["Audio"])

def stereo_to_mono(audio_bytes: bytes) -> bytes:
    """
    Converts 16-bit PCM stereo to mono.
    Assumes little-endian signed 16-bit samples.
    """
    samples = np.frombuffer(audio_bytes, dtype=np.int16)
    if len(samples) % 2 != 0:
        samples = samples[:-1]  # remove last sample if uneven
    left = samples[0::2]
    right = samples[1::2]
    mono = ((left.astype(np.int32) + right.astype(np.int32)) // 2).astype(np.int16)
    return mono.tobytes()


@router.post("/transcribe")
async def transcribe_audio_stream(request: Request):
    """
    Receives raw 16-bit PCM stereo audio stream (application/octet-stream) from ESP32
    and returns a plain text response.
    """
    audio_data = await request.body()
    
    if len(audio_data) == 0:
        raise HTTPException(status_code=400, detail="No audio data received.")
        
    print(f"Received {len(audio_data)} bytes of audio.")

    # 1️⃣ Convert stereo to mono if needed
    try:
        audio_data = stereo_to_mono(audio_data)
    except Exception as e:
        print(f"Failed to convert audio to mono: {e}")
        raise HTTPException(status_code=500, detail="Audio conversion failed.")

    # 2️⃣ Transcribe the audio
    try:
        transcription = transcribe_short_audio_sync(
            audio_content=audio_data,
            sample_rate_hertz=16000  # make sure this matches your ESP32
        )
        
        # 3️⃣ Generate response text
        response_text = "I did not understand that."  # default
        
        if "turn on" in transcription.lower():
            response_text = "Okay, turning on the light."
            # TODO: control your device here
        elif "turn off" in transcription.lower():
            response_text = "Got it, turning off the light."
            # TODO: control your device here
        elif transcription:
            response_text = f"I heard you say: {transcription}"

    except Exception as e:
        print(f"Transcription Failed: {e}")
        response_text = "Sorry, I had an error processing the audio."

    return Response(content=response_text, media_type="text/plain")
