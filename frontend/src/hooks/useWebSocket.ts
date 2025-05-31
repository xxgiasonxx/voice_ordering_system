import { useCallback, useEffect, useRef, useState } from 'react';
import { TranscriptMessage } from '@/interfaces/whisper';

interface UseWebSocketProps {
  url: string;
  onMessage: (data: TranscriptMessage) => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
}

export const useWebSocket = ({ url, onMessage, onError, onClose }: UseWebSocketProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const websocketRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data: TranscriptMessage = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('解析 WebSocket 訊息失敗:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket 錯誤:', error);
      onError?.(error);
    };

    ws.onclose = () => {
      setIsConnected(false);
      onClose?.();
    };

    websocketRef.current = ws;
  }, [url, onMessage, onError, onClose]);

  const disconnect = useCallback(() => {
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
      setIsConnected(false);
    }
  }, []);

  const send = useCallback((data: ArrayBuffer) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(data);
    }
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    connect,
    disconnect,
    send
  };
};