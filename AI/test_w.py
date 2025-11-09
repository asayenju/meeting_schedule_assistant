import httpx
import os

API_URL = "http://172.31.81.117:8000/api/audio/transcribe"
WAV_FILE_NAME = "test.wav"

def test_audio_post():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    wav_file_path = os.path.join(script_dir, WAV_FILE_NAME)

    with open(wav_file_path, "rb") as f:
        audio_data = f.read()

    print(f"Loaded {len(audio_data)} bytes from {wav_file_path}")

    headers = {"Content-Type": "application/octet-stream"}
    response = httpx.post(API_URL, headers=headers, content=audio_data, timeout=30.0)

    print("Status:", response.status_code)
    print("Response text:", response.text)

if __name__ == "__main__":
    test_audio_post()
