import React, { useState, useEffect, useRef } from 'react';
import Loading from '@/pages/Loading'
import { useToken } from '@/contexts/TokenContext'; // 假設你有一個 useToken hook

export const LiveTranscription: React.FC = () => {
  const {token, isLoading} = useToken();
  const [status, setStatus] = useState<string>('Disconnected');
  const [transcript, setTranscript] = useState<string>('');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const socketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);


  useEffect(() => {
    let isMounted = true;
    
    const initializeAudio = async () => {
      try {
        // 確保之前的連接已關閉
        if (socketRef.current) {
          socketRef.current.close();
          socketRef.current = null;
        }

        // Check browser support
        if (!MediaRecorder.isTypeSupported('audio/webm')) {
          setError('Browser not supported');
          return;
        }

        // Get user media
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        if (!isMounted) {
          stream.getTracks().forEach(track => track.stop());
          return;
        }
        streamRef.current = stream;

        // Create media recorder
        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: 'audio/webm',
        });
        mediaRecorderRef.current = mediaRecorder;

        // Create WebSocket connection
        const socket = new WebSocket(`ws://localhost:8000/asr?encrypted_token=${token}`);
        socketRef.current = socket;

        // WebSocket event handlers
        socket.onopen = () => {
          if (!isMounted) return;
          setStatus('Connected');
          setIsConnected(true);
          console.log({ event: 'onopen' });

          // Start recording when connected
          mediaRecorder.addEventListener('dataavailable', async (event) => {
            if (event.data.size > 0 && socket.readyState === 1) {
              socket.send(event.data);
            }
          });
          mediaRecorder.start(250);
        };

        socket.onmessage = (message) => {
          if (!isMounted) return;
          const received = message.data;
          if (received) {
            console.log(received);
            setTranscript(prev => prev + ' ' + received);
          }
        };

        socket.onclose = () => {
          if (!isMounted) return;
          console.log({ event: 'onclose' });
          setStatus('Disconnected');
          setIsConnected(false);
        };

        socket.onerror = (error) => {
          if (!isMounted) return;
          console.log({ event: 'onerror', error });
          setError('WebSocket connection error');
          setStatus('Error');
          setIsConnected(false);
        };

      } catch (err) {
        if (!isMounted) return;
        console.error('Error initializing audio:', err);
        setError('Failed to access microphone');
      }
    };

    initializeAudio();

    // Cleanup function
    return () => {
      isMounted = false;
      
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []); // 空依賴數組確保只執行一次

  const clearTranscript = () => {
    setTranscript('');
  };

  return (
    isLoading ? <Loading /> :
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Live Transcription
          </h1>
          <p className="text-gray-600 mb-6">
            Transcribe Audio With FastAPI
          </p>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 font-medium">Error:</p>
              <p className="text-red-600">{error}</p>
            </div>
          )}

          {/* Status Indicator */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <span className="font-medium text-gray-700">Connection Status:</span>
              <span className={`font-semibold ${
                isConnected ? 'text-green-600' : 'text-red-600'
              }`}>
                {status}
              </span>
            </div>
          </div>

          {/* Controls */}
          <div className="mb-6">
            <button
              onClick={clearTranscript}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium 
                       hover:bg-blue-700 transition-colors duration-200"
            >
              Clear Transcript
            </button>
          </div>

          {/* Transcript Display */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Live Transcript
            </h2>
            <div className="min-h-32 max-h-64 overflow-y-auto bg-white p-4 rounded border">
              {transcript ? (
                <p className="text-gray-800 leading-relaxed">{transcript}</p>
              ) : (
                <p className="text-gray-500 italic">
                  Transcript will appear here as you speak...
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveTranscription;
