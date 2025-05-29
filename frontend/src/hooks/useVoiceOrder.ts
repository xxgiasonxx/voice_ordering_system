import { useState, useEffect, useRef } from "react";
import WaveSurfer from "wavesurfer.js";

export interface VoiceOrderState {
  isRecording: boolean;
  transcript: string;
  response: string;
  isSpeaking: boolean;
  startListening: () => void;
  stopListening: () => void;
}

export const useVoiceOrder = (waveSurferRef: React.RefObject<WaveSurfer>) => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
        audioBitsPerSecond: 16000, // 16kHz，符合 Faster Whisper
      });

      const baseUrl: string = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
      const wsUrl = baseUrl.replace(/^http/, "ws") + "/ws/audio";

      socketRef.current = new WebSocket(wsUrl);
      socketRef.current.onopen = () => {
        setIsRecording(true);
        if (mediaRecorderRef.current?.state !== "recording") {
          mediaRecorderRef.current?.start(300); // 每 300ms 傳送音訊分段
        }
        // mediaRecorderRef.current?.start(300); // 每 300ms 傳送音訊分段
      };

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0 && socketRef.current?.readyState === WebSocket.OPEN) {
          socketRef.current.send(event.data); // 傳送音訊分段
        }
      };

      socketRef.current.onmessage = async (event) => {
        if (typeof event.data === "string") {
          const data = JSON.parse(event.data);
          if (data.text) setTranscript(data.text);
          if (data.response) setResponse(data.response);
        } else {
          // 處理語音回應
          if (currentAudioRef.current) {
            currentAudioRef.current.pause(); // 中斷當前播放
            currentAudioRef.current = null;
          }
          const audioBlob = new Blob([event.data], { type: "audio/wav" });
          currentAudioRef.current = new Audio(URL.createObjectURL(audioBlob));
          setIsSpeaking(true);
          currentAudioRef.current.onended = () => {
            setIsSpeaking(false);
            if (mediaRecorderRef.current?.state !== "recording") {
              mediaRecorderRef.current?.start(300); // 繼續錄音
            }
          };
          currentAudioRef.current.play();
        }
      };

      socketRef.current.onclose = () => {
        setIsRecording(false);
        mediaRecorderRef.current?.stop();
      };

      socketRef.current.onerror = (error) => {
        console.error("WebSocket error:", error);
        stopListening();
      };

      // 更新 WaveSurfer 波形
      const audioContext = new AudioContext({ sampleRate: 16000 });
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      source.connect(analyser);
      const dataArray = new Uint8Array(analyser.fftSize);

      const updateWaveform = () => {
        if (!isRecording || !waveSurferRef.current) return;
        analyser.getByteFrequencyData(dataArray);
        const blob = new Blob([dataArray.buffer], { type: "audio/wav" });
        waveSurferRef.current.loadBlob(blob);
        requestAnimationFrame(updateWaveform);
      };
      updateWaveform();
    } catch (error) {
      console.error("Error starting audio:", error);
    }
  };

  const stopListening = () => {
    if (socketRef.current) socketRef.current.close();
    if (mediaRecorderRef.current) mediaRecorderRef.current.stop();
    setIsRecording(false);
  };

  useEffect(() => {
    startListening();
    return () => stopListening();
  }, []);

  return { isRecording, transcript, response, isSpeaking, startListening, stopListening };
};