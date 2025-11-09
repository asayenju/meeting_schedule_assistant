from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import tempfile
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

# ElevenLabs API configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_URL = "https://api.elevenlabs.io/v1/speech-to-text"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            # Prepare request to ElevenLabs API
            headers = {
                "xi-api-key": ELEVENLABS_API_KEY
            }
            
            with open(tmp_path, "rb") as f:
                files = {
                    "file": f
                }
                
                data = {
                    "model_id": "scribe_v1",
                    "language_code": "eng",
                    "tag_audio_events": True,
                    "diarize": True
                }
                
                response = requests.post(ELEVENLABS_URL, headers=headers, files=files, data=data)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            if response.status_code == 200:
                result = response.json()
                transcribed_text = result.get('text', '')
                
                # Call agent API with the transcribed text
                agent_response = None
                if transcribed_text:
                    try:
                        agent_api_url = "http://localhost:8001/get-response"
                        print(f"Calling agent API with text: {transcribed_text[:50]}...")
                        agent_response_data = requests.post(
                            agent_api_url,
                            json={"input": transcribed_text},
                            timeout=30
                        )
                        agent_response_data.raise_for_status()
                        agent_result = agent_response_data.json()
                        agent_response = agent_result.get('response', 'No response from agent')
                        print(f"Agent API response: {agent_response[:100] if agent_response else 'None'}...")
                    except requests.exceptions.ConnectionError as e:
                        print(f"Connection error calling agent API: {e}")
                        agent_response = f"Error: Could not connect to agent API. Is it running on port 8001?"
                    except requests.exceptions.Timeout as e:
                        print(f"Timeout calling agent API: {e}")
                        agent_response = f"Error: Agent API request timed out."
                    except requests.exceptions.RequestException as e:
                        print(f"Error calling agent API: {e}")
                        agent_response = f"Error calling agent API: {str(e)}"
                else:
                    agent_response = "No transcription text to send to agent"
                
                return jsonify({
                    'success': True,
                    'text': transcribed_text,
                    'agent_response': agent_response,
                    'full_result': result
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'API Error: {response.status_code}',
                    'details': response.text
                }), response.status_code
                
        except Exception as e:
            # Clean up temporary file in case of error
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise e
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

