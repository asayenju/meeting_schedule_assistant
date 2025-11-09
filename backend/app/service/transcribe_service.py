# backend/app/services/test_transcribe.py (RUN THIS FILE)

import os
import sys
from google.cloud import speech

# --- Dynamic Path Setup (Copied from transcribe_service.py) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Define the name of the service account key file
SERVICE_ACCOUNT_FILE_NAME = 'service-key.json' 
SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, SERVICE_ACCOUNT_FILE_NAME)

# 2. CRITICAL: Set the environment variable
if os.path.exists(SERVICE_ACCOUNT_PATH):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = SERVICE_ACCOUNT_PATH
else:
    print(f"FATAL ERROR: Service Account key not found at {SERVICE_ACCOUNT_PATH}")
    sys.exit(1) # Stop execution if key is missing

# --- Client Initialization ---
try:
    speech_client = speech.SpeechClient()
    print("Client initialized successfully.")
except Exception as e:
    print(f"FATAL ERROR: Failed to initialize Google SpeechClient: {e}")
    sys.exit(1) # Stop execution if auth fails

# --- Transcription Function (Your Logic) ---
def transcribe_short_audio_sync(audio_content: bytes, sample_rate_hertz: int = 44100) -> str:
    """Performs synchronous transcription on audio content (<= 60 seconds)."""
    
    audio = speech.RecognitionAudio(content=audio_content)
    
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate_hertz,
        language_code="en-US",
    )

    response = speech_client.recognize(config=config, audio=audio)
    
    return "\n".join([result.alternatives[0].transcript for result in response.results])

# =================================================================
# === TEST EXECUTION BLOCK (MAKES IT RUN) ==========================
# =================================================================

TEST_AUDIO_FILE = 'harvard_mono.wav' 
SAMPLE_RATE = 44100

if __name__ == "__main__":
    print("\n--- Starting Speech-to-Text Test ---")
    
    audio_path = os.path.join(BASE_DIR, TEST_AUDIO_FILE)

    if not os.path.exists(audio_path):
        print(f"❌ ERROR: Test audio file '{TEST_AUDIO_FILE}' not found.")
        print("Please ensure your 16kHz WAV file is in this folder.")
        sys.exit(1)

    # 1. Read the audio content
    print(f"Reading audio file: {TEST_AUDIO_FILE}...")
    try:
        with open(audio_path, 'rb') as f:
            audio_content = f.read()
    except Exception as e:
        print(f"❌ ERROR: Could not read audio file: {e}")
        sys.exit(1)

    # 2. Call the transcription service
    print(f"Sending {len(audio_content)} bytes to Google STT...")
    try:
        transcription_result = transcribe_short_audio_sync(
            audio_content=audio_content,
            sample_rate_hertz=SAMPLE_RATE
        )
        
        # 3. Display results
        print("\n✅ SUCCESS: Transcription Received!")
        print("-----------------------------------")
        print(f"Result: \"{transcription_result.strip()}\"")
        print("-----------------------------------\n")

    except Exception as e:
        print("\n❌ FAILED: Transcription Error!")
        print(f"Error Details: {e}")
        print("\n* Double-check the Cloud Speech API is enabled.")
        print("* Verify your audio file is 44100 Hz and <= 60 seconds.")