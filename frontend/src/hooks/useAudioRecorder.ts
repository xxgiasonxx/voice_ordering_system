import { useCallback, useRef, useState } from 'react';
import { AudioConfig } from '@/interfaces/whisper';

interface UseAudioRecorderProps {
  onAudioData: (data: ArrayBuffer) => void;
  audioConfig?: Partial<AudioConfig>;
}

export const useAudioRecorder = ({ 
  onAudioData, 
  audioConfig = {} 
}: UseAudioRecorderProps) => {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const defaultConfig: AudioConfig = {
    sampleRate: 16000,
    channelCount: 1,
    echoCancellation: true,
    noiseSuppression: true,
    ...audioConfig
  };

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      
      // 獲取麥克風權限
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: defaultConfig
      });
      
      streamRef.current = stream;
      
      // 創建 AudioContext
      audioContextRef.current = new AudioContext({ 
        sampleRate: defaultConfig.sampleRate 
      });
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      
      // 創建音頻處理器 (注意: ScriptProcessorNode 已被棄用，但為了兼容性仍可使用)
      processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      
      processorRef.current.onaudioprocess = (event) => {
        const inputData = event.inputBuffer.getChannelData(0);
        const buffer = new ArrayBuffer(inputData.length * 2);
        const view = new Int16Array(buffer);
        
        // 轉換為 16-bit PCM
        for (let i = 0; i < inputData.length; i++) {
          view[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
        }
        
        onAudioData(buffer);
      };
      
      source.connect(processorRef.current);
      processorRef.current.connect(audioContextRef.current.destination);
      
      setIsRecording(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '獲取麥克風權限失敗';
      setError(errorMessage);
      console.error('開始錄音失敗:', err);
    }
  }, [onAudioData, defaultConfig]);

  const stopRecording = useCallback(() => {
    // 停止音頻處理器
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    
    // 關閉 AudioContext
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    // 停止媒體流
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    setIsRecording(false);
  }, []);

  return {
    isRecording,
    error,
    startRecording,
    stopRecording
  };
};