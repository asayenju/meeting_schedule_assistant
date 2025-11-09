import httpx
import os
from pathlib import Path

# --- Configuration ---
# IMPORTANT: Use the correct IP address for your FastAPI server
API_URL = "http://172.30.151.186:8000/api/audio/transcribe"
WAV_FILE_NAME = "umass_4.wav"

def test_audio_post():
    """
    Sends the WAV file as a multipart/form-data upload,
    matching the FastAPI endpoint's expectation (UploadFile = File(...)).
    """
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    wav_file_path = script_dir / WAV_FILE_NAME

    if not wav_file_path.exists():
        print(f"Error: WAV file not found at {wav_file_path}")
        return

    print(f"Attempting to upload {wav_file_path}...")

    # Open the file and prepare it for the 'files' parameter
    # The key 'audio_file' here corresponds to the argument name in the FastAPI function:
    # @router.post("/transcribe") async def transcribe_audio_file(audio_file: UploadFile = File(...)):
    files = {
        'audio_file': (
            WAV_FILE_NAME,                  # Filename
            open(wav_file_path, 'rb'),      # File handle (the actual data)
            'audio/wav'                     # Content-Type for this specific part
        )
    }

    # httpx automatically sets the overall Content-Type header to 
    # 'multipart/form-data' when the 'files' parameter is used.
    try:
        response = httpx.post(API_URL, files=files, timeout=30.0)
        
        print("\n--- Response ---")
        print("Status:", response.status_code)
        print("Response text:", response.text)
        print("----------------")

    except httpx.HTTPError as e:
        print(f"\nAn HTTP error occurred: {e}")
    finally:
        # Ensure the file handle is closed after the request is finished
        files['audio_file'][1].close()


if __name__ == "__main__":
    test_audio_post()