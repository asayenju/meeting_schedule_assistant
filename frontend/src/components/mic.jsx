import React, { useState, useRef } from "react";
import { Mic, StopCircle, Loader2, Settings, Volume2, Trash2 } from "lucide-react";

export default function VoiceAssistant() {
  const [recording, setRecording] = useState(false);
  const [audioURL, setAudioURL] = useState(null);
  const [aiResponse, setAiResponse] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [config, setConfig] = useState({
    apiEndpoint: "http://172.30.151.186:8000/api/audio/transcribe",
    audioFormat: "audio/wav",
    autoSubmit: true,
    showAudioPlayer: true,
    sampleRate: 16000,
  });
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);

  async function startRecording() {
    setError(null);
    setAiResponse("");
    setAudioURL(null);
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: config.sampleRate,
          channelCount: 1, // Mono audio
        } 
      });
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        
        const blob = new Blob(audioChunksRef.current, { type: config.audioFormat });
        const url = URL.createObjectURL(blob);
        setAudioURL(url);

        if (config.autoSubmit) {
          await submitAudio(blob);
        }
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (err) {
      setError("Microphone access denied or not available. Please check your browser permissions.");
      console.error("Recording error:", err);
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  }

  async function submitAudio(blob) {
    try {
      setLoading(true);
      
      // Convert blob to AudioBuffer for proper PCM conversion
      const arrayBuffer = await blob.arrayBuffer();
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      
      // Convert to mono if stereo
      let channelData;
      if (audioBuffer.numberOfChannels === 2) {
        // Average the two channels
        const left = audioBuffer.getChannelData(0);
        const right = audioBuffer.getChannelData(1);
        channelData = new Float32Array(left.length);
        for (let i = 0; i < left.length; i++) {
          channelData[i] = (left[i] + right[i]) / 2;
        }
      } else {
        channelData = audioBuffer.getChannelData(0);
      }
      
      // Convert float32 samples to int16 PCM
      const pcmData = new Int16Array(channelData.length);
      for (let i = 0; i < channelData.length; i++) {
        // Clamp to [-1, 1] and convert to int16
        const s = Math.max(-1, Math.min(1, channelData[i]));
        pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      
      const res = await fetch(config.apiEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/octet-stream",
        },
        body: pcmData.buffer,
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Server returned ${res.status}: ${errorText}`);
      }
      
      // The backend returns plain text response
      const responseText = await res.text();
      setAiResponse(responseText);
    } catch (err) {
      setError(`Failed to process audio: ${err.message}`);
      console.error("API error:", err);
    } finally {
      setLoading(false);
    }
  }

  function clearAll() {
    setAudioURL(null);
    setAiResponse("");
    setError(null);
    if (audioURL) {
      URL.revokeObjectURL(audioURL);
    }
  }

  function updateConfig(key, value) {
    setConfig(prev => ({ ...prev, [key]: value }));
  }

  return (
    <div style={styles.pageContainer}>
      <div style={styles.container}>
        <button
          onClick={() => setShowSettings(!showSettings)}
          style={styles.settingsBtn}
          title="Configuration"
        >
          <Settings style={{
            ...styles.settingsIcon,
            transform: showSettings ? 'rotate(90deg)' : 'rotate(0deg)'
          }} />
        </button>

        {showSettings && (
          <div style={styles.settingsPanel}>
            <h3 style={styles.settingsTitle}>Configuration</h3>
            
            <div style={styles.settingGroup}>
              <label style={styles.label}>API Endpoint</label>
              <input
                type="text"
                value={config.apiEndpoint}
                onChange={(e) => updateConfig('apiEndpoint', e.target.value)}
                style={styles.input}
                placeholder="/api/audio"
              />
            </div>

            <div style={styles.settingGroup}>
              <label style={styles.label}>Sample Rate (Hz)</label>
              <select
                value={config.sampleRate}
                onChange={(e) => updateConfig('sampleRate', parseInt(e.target.value))}
                style={styles.select}
              >
                <option value="8000">8000 Hz</option>
                <option value="16000">16000 Hz (Recommended)</option>
                <option value="44100">44100 Hz</option>
                <option value="48000">48000 Hz</option>
              </select>
            </div>

            <div style={styles.checkboxGroup}>
              <input
                type="checkbox"
                id="autoSubmit"
                checked={config.autoSubmit}
                onChange={(e) => updateConfig('autoSubmit', e.target.checked)}
                style={styles.checkbox}
              />
              <label htmlFor="autoSubmit" style={styles.checkboxLabel}>
                Auto-submit recording when stopped
              </label>
            </div>

            <div style={styles.checkboxGroup}>
              <input
                type="checkbox"
                id="showAudioPlayer"
                checked={config.showAudioPlayer}
                onChange={(e) => updateConfig('showAudioPlayer', e.target.checked)}
                style={styles.checkbox}
              />
              <label htmlFor="showAudioPlayer" style={styles.checkboxLabel}>
                Show audio player after recording
              </label>
            </div>
          </div>
        )}

        <div style={styles.header}>
          <h1 style={styles.title}>Voice Assistant</h1>
          <p style={styles.subtitle}>
            Click the microphone to start recording. Your voice will be transcribed and analyzed by AI.
          </p>
        </div>

        <div style={styles.recordingSection}>
          <div style={{
            ...styles.micButton,
            background: recording 
              ? 'linear-gradient(135deg, #ef4444, #ec4899)' 
              : 'linear-gradient(135deg, #3b82f6, #4f46e5)',
            boxShadow: recording
              ? '0 10px 40px rgba(239, 68, 68, 0.4)'
              : '0 10px 40px rgba(59, 130, 246, 0.4)',
            animation: recording ? 'pulse 1.5s infinite' : 'none'
          }}>
            {recording ? (
              <StopCircle style={styles.micIcon} />
            ) : (
              <Mic style={styles.micIcon} />
            )}
          </div>

          <button
            onClick={recording ? stopRecording : startRecording}
            disabled={loading}
            style={{
              ...styles.actionButton,
              background: recording
                ? 'linear-gradient(135deg, #ef4444, #ec4899)'
                : 'linear-gradient(135deg, #3b82f6, #4f46e5)',
              opacity: loading ? 0.5 : 1,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? (
              <span style={styles.buttonContent}>
                <Loader2 style={styles.spinIcon} />
                Processing...
              </span>
            ) : recording ? (
              <span style={styles.buttonContent}>
                <StopCircle style={styles.buttonIcon} />
                Stop Recording
              </span>
            ) : (
              <span style={styles.buttonContent}>
                <Mic style={styles.buttonIcon} />
                Start Recording
              </span>
            )}
          </button>
        </div>

        {audioURL && config.showAudioPlayer && (
          <div style={styles.audioSection}>
            <div style={styles.audioHeader}>
              <Volume2 style={styles.volumeIcon} />
              <span style={styles.audioLabel}>Recorded Audio</span>
            </div>
            <audio controls src={audioURL} style={styles.audioPlayer}></audio>
          </div>
        )}

        {audioURL && !config.autoSubmit && !loading && !aiResponse && (
          <div style={styles.submitSection}>
            <button
              onClick={() => {
                fetch(audioURL)
                  .then(res => res.blob())
                  .then(blob => submitAudio(blob));
              }}
              style={styles.submitButton}
            >
              Submit Audio for Processing
            </button>
          </div>
        )}

        {recording && (
          <div style={styles.recordingStatus}>
            <div style={styles.recordingDot}></div>
            Recording in progress...
          </div>
        )}

        {error && (
          <div style={styles.errorBox}>
            <span style={styles.errorIcon}>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <div style={styles.responseSection}>
          <div style={styles.responseHeader}>
            <div style={styles.responseHeaderLeft}>
              <div style={styles.responseBar}></div>
              <h2 style={styles.responseTitle}>AI Response</h2>
            </div>
            {(audioURL || aiResponse) && (
              <button onClick={clearAll} style={styles.clearButton}>
                <Trash2 style={styles.trashIcon} />
                Clear
              </button>
            )}
          </div>
          <div style={styles.responseBox}>
            {aiResponse ? (
              <span>{aiResponse}</span>
            ) : (
              <span style={styles.placeholder}>
                {loading ? "Processing your audio..." : "Your AI response will appear here"}
              </span>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
      `}</style>
    </div>
  );
}

const styles = {
  pageContainer: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '24px',
    background: 'linear-gradient(to bottom right, #e3f2fd, #fff9c4)',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  },
  container: {
    width: '100%',
    maxWidth: '700px',
    padding: '40px',
    borderRadius: '24px',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)',
    background: 'rgba(255, 255, 255, 0.95)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    position: 'relative',
    animation: 'fadeIn 0.5s ease-out'
  },
  settingsBtn: {
    position: 'absolute',
    top: '24px',
    right: '24px',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: '8px',
    borderRadius: '12px',
    transition: 'background 0.3s'
  },
  settingsIcon: {
    width: '20px',
    height: '20px',
    color: '#6b7280',
    transition: 'transform 0.3s'
  },
  settingsPanel: {
    marginBottom: '24px',
    padding: '24px',
    background: 'linear-gradient(to bottom right, #e3f2fd, #e8eaf6)',
    borderRadius: '16px',
    border: '2px solid #90caf9'
  },
  settingsTitle: {
    fontSize: '18px',
    fontWeight: 'bold',
    marginBottom: '16px',
    color: '#1e3a8a'
  },
  settingGroup: {
    marginBottom: '16px'
  },
  label: {
    display: 'block',
    fontSize: '14px',
    fontWeight: '600',
    color: '#374151',
    marginBottom: '8px'
  },
  input: {
    width: '100%',
    padding: '10px 16px',
    border: '2px solid #e5e7eb',
    borderRadius: '12px',
    fontSize: '14px',
    transition: 'border-color 0.3s'
  },
  select: {
    width: '100%',
    padding: '10px 16px',
    border: '2px solid #e5e7eb',
    borderRadius: '12px',
    fontSize: '14px',
    transition: 'border-color 0.3s',
    background: 'white'
  },
  checkboxGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginTop: '16px'
  },
  checkbox: {
    width: '20px',
    height: '20px',
    cursor: 'pointer'
  },
  checkboxLabel: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#374151',
    cursor: 'pointer'
  },
  header: {
    textAlign: 'center',
    marginBottom: '32px'
  },
  title: {
    fontSize: '36px',
    fontWeight: 'bold',
    marginBottom: '12px',
    background: 'linear-gradient(to right, #2563eb, #d97706)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text'
  },
  subtitle: {
    color: '#6b7280',
    fontSize: '16px'
  },
  recordingSection: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '24px',
    marginBottom: '32px'
  },
  micButton: {
    width: '128px',
    height: '128px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative'
  },
  micIcon: {
    width: '64px',
    height: '64px',
    color: 'white',
    strokeWidth: 2
  },
  actionButton: {
    padding: '16px 32px',
    borderRadius: '16px',
    fontSize: '18px',
    fontWeight: '600',
    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.2)',
    transition: 'all 0.3s',
    border: 'none',
    color: 'white'
  },
  buttonContent: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  buttonIcon: {
    width: '20px',
    height: '20px'
  },
  spinIcon: {
    width: '20px',
    height: '20px',
    animation: 'spin 1s linear infinite'
  },
  audioSection: {
    marginBottom: '24px'
  },
  audioHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px'
  },
  volumeIcon: {
    width: '16px',
    height: '16px',
    color: '#6b7280'
  },
  audioLabel: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#374151'
  },
  audioPlayer: {
    width: '100%',
    borderRadius: '12px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
  },
  submitSection: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: '24px'
  },
  submitButton: {
    padding: '12px 24px',
    background: 'linear-gradient(135deg, #10b981, #059669)',
    color: 'white',
    borderRadius: '12px',
    fontWeight: '600',
    boxShadow: '0 10px 30px rgba(16, 185, 129, 0.3)',
    transition: 'all 0.3s',
    border: 'none',
    cursor: 'pointer'
  },
  recordingStatus: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    color: '#dc2626',
    fontWeight: '600',
    marginBottom: '16px',
    padding: '16px',
    background: '#fee2e2',
    borderRadius: '12px'
  },
  recordingDot: {
    width: '12px',
    height: '12px',
    background: '#dc2626',
    borderRadius: '50%',
    animation: 'pulse 1.5s infinite'
  },
  errorBox: {
    padding: '16px',
    background: '#fee2e2',
    border: '2px solid #fca5a5',
    borderRadius: '12px',
    color: '#b91c1c',
    fontSize: '14px',
    marginBottom: '16px',
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px'
  },
  errorIcon: {
    fontSize: '18px'
  },
  responseSection: {
    marginTop: '32px'
  },
  responseHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '12px'
  },
  responseHeaderLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  responseBar: {
    width: '4px',
    height: '24px',
    background: 'linear-gradient(to bottom, #2563eb, #4f46e5)',
    borderRadius: '4px'
  },
  responseTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#1f2937'
  },
  clearButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 12px',
    fontSize: '14px',
    color: '#dc2626',
    background: 'none',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'background 0.3s'
  },
  trashIcon: {
    width: '16px',
    height: '16px'
  },
  responseBox: {
    minHeight: '160px',
    padding: '24px',
    background: 'linear-gradient(to bottom right, #f9fafb, #dbeafe)',
    border: '2px solid #e5e7eb',
    borderRadius: '16px',
    color: '#1f2937',
    whiteSpace: 'pre-line',
    boxShadow: 'inset 0 2px 8px rgba(0, 0, 0, 0.05)'
  },
  placeholder: {
    color: '#9ca3af',
    fontStyle: 'italic'
  }
};