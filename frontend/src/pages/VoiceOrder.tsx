import React, { useState, useEffect, useRef } from 'react';
import Loading from '@/pages/Loading';
import Header from '@/components/Header';
import { CloseIcon, MicIcon } from '@/components/Icon';
import Logo from '@/assets/Logo.png';
import menuImageUrl from "../assets/176172344.jpg";
import { useToken } from '@/contexts/TokenContext';
import { Link } from 'react-router-dom';
import axios from 'axios';

interface ChatMessage {
  id: number;
  type: 'user' | 'bot';
  message: string;
  timestamp: Date;
}

interface WebSocketMessage {
  type: 'cus' | 'llm' | 'error' | 'close' | 'success' | 'end' | "order";
  transcript?: string;
  response?: string;
  msg?: string;
  diff?: Array<any>;
}

interface HistoryMessage {
  type: 'llm' | 'cus';
  response?: string;
  transcript?: string;
  time: string;
}

interface HistoryResponse {
  conversation: HistoryMessage[];
}

// --- 核心轉換函式：將 Float32 轉換為 Int16 ---
const float32ToInt16 = (buffer: Float32Array): ArrayBuffer => {
    let l = buffer.length;
    const buf = new Int16Array(l);
    while (l--) {
        buf[l] = Math.min(1, buffer[l]) * 0x7FFF;
    }
    return buf.buffer;
};

export const LiveTranscription: React.FC = () => {
  const { isLoading } = useToken();
  const [transcript, setTranscript] = useState<string>('');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showChat, setShowChat] = useState(false);
  const [showWelcomePrompt, setShowWelcomePrompt] = useState(true);
  const [imageScale, setImageScale] = useState(1);
  const [imagePosition, setImagePosition] = useState({ x: 0, y: 0 });
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      type: 'bot',
      message: '您好！歡迎使用語音點餐系統，請參考上方菜單並告訴我您想要什麼餐點？',
      timestamp: new Date()
    }
  ]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const socketRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isReconnectingRef = useRef<boolean>(false);
  const isMountedRef = useRef<boolean>(true);
  
  const lastTouchDistance = useRef<number>(0);
  const isDragging = useRef<boolean>(false);
  const lastTouchPosition = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const loadConversationHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const baseUrl: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await axios(`${baseUrl}/history`, {
        withCredentials: true,
      });
      if (response.status !== 200) {
        throw new Error('Failed to fetch conversation history');
      }

      const data: HistoryResponse = response.data;
      if (!data || !data.conversation) {
        console.warn('No conversation history found');
        return;
      }
      if (data.conversation && data.conversation.length > 0) {
        const historyMessages: ChatMessage[] = data.conversation.map((msg, index) => ({
          id: index + 1,
          type: msg.type === 'cus' ? 'user' as const : 'bot' as const,
          message: msg.type === 'cus' ? (msg.transcript || '') : (msg.response || ''),
          timestamp: new Date(msg.time)
        })).filter(msg => msg.message.trim() !== '');
        
        setChatMessages([
          ...historyMessages
        ]);
      }
    } catch (error) {
      console.error('Error loading conversation history:', error);
      setError('載入歷史對話失敗');
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const getDistance = (touch1: React.Touch, touch2: React.Touch) => {
    const dx = touch1.clientX - touch2.clientX;
    const dy = touch1.clientY - touch2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      e.preventDefault();
      const distance = getDistance(e.touches[0], e.touches[1]);
      lastTouchDistance.current = distance;
    } else if (e.touches.length === 1 && imageScale > 1) {
      isDragging.current = true;
      lastTouchPosition.current = {
        x: e.touches[0].clientX,
        y: e.touches[0].clientY
      };
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      e.preventDefault();
      const distance = getDistance(e.touches[0], e.touches[1]);
      const scaleDelta = distance / lastTouchDistance.current;
      const newScale = Math.min(Math.max(imageScale * scaleDelta, 0.5), 4);
      
      setImageScale(newScale);
      lastTouchDistance.current = distance;
    } else if (e.touches.length === 1 && isDragging.current && imageScale > 1) {
      e.preventDefault();
      const deltaX = e.touches[0].clientX - lastTouchPosition.current.x;
      const deltaY = e.touches[0].clientY - lastTouchPosition.current.y;
      
      setImagePosition(prev => ({
        x: prev.x + deltaX / imageScale,
        y: prev.y + deltaY / imageScale
      }));
      
      lastTouchPosition.current = {
        x: e.touches[0].clientX,
        y: e.touches[0].clientY
      };
    }
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (e.touches.length < 2) {
      lastTouchDistance.current = 0;
    }
    if (e.touches.length === 0) {
      isDragging.current = false;
    }
  };

  const handleDoubleClick = () => {
    if (imageScale === 1) {
      setImageScale(2);
    } else {
      resetImagePosition();
    }
  };

  const resetImagePosition = () => {
    setImageScale(1);
    setImagePosition({ x: 0, y: 0 });
  };

  const startVoiceOrdering = () => {
    setShowWelcomePrompt(false);
    // *** UX OPTIMIZATION: Immediately provide feedback to the user ***
    setError("正在準備語音引擎，請稍候...");
    setIsConnected(false);
  };

  const attemptReconnect = (retryCount = 0) => {
    const maxRetries = 5;
    const baseDelay = 1000;
    
    if (!isMountedRef.current || retryCount >= maxRetries || isReconnectingRef.current) {
      return;
    }
    
    isReconnectingRef.current = true;
    const delay = Math.min(baseDelay * Math.pow(2, retryCount), 30000);
    
    console.log(`Attempting to reconnect... (${retryCount + 1}/${maxRetries})`);
    setError(`連接中斷，正在重新連接... (${retryCount + 1}/${maxRetries})`);
    
    reconnectTimeoutRef.current = setTimeout(async () => {
      try {
        await initializeAudio();
        isReconnectingRef.current = false;
      } catch (error) {
        console.error('Reconnection failed:', error);
        isReconnectingRef.current = false;
        attemptReconnect(retryCount + 1);
      }
    }, delay);
  };

  const stopAudioProcessing = () => {
      if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
      }
      if (scriptProcessorRef.current) {
          scriptProcessorRef.current.disconnect();
          scriptProcessorRef.current = null;
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
          audioContextRef.current.close();
          audioContextRef.current = null;
      }
  };

  const initializeAudio = async () => {
    try {
      if (socketRef.current) {
        socketRef.current.close();
      }
      stopAudioProcessing();

      const SAMPLE_RATE = 16000;
      const BUFFER_SIZE = 4096;

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
        }
      });
      if (!isMountedRef.current) { stream.getTracks().forEach(track => track.stop()); return; }
      streamRef.current = stream;

      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      const context = new AudioCtx({ sampleRate: SAMPLE_RATE });
      audioContextRef.current = context;
      
      const source = context.createMediaStreamSource(stream);
      const processor = context.createScriptProcessor(BUFFER_SIZE, 1, 1);
      scriptProcessorRef.current = processor;
      
      const socket = new WebSocket(`ws://localhost:8000/asr`);
      socketRef.current = socket;

      socket.onopen = () => {
        if (!isMountedRef.current) return;
        console.log('WebSocket connected successfully. Audio processing will start.');
        // *** UX OPTIMIZATION: Update state only when fully ready ***
        setIsConnected(true);
        setError(null); // Clear "preparing..." message
        isReconnectingRef.current = false;

        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }

        // Start processing audio only after the connection is fully open
        processor.onaudioprocess = (audioProcessingEvent) => {
            if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                const inputData = audioProcessingEvent.inputBuffer.getChannelData(0);
                const pcmData = float32ToInt16(inputData);
                socketRef.current.send(pcmData);
            }
        };

        source.connect(processor);
        processor.connect(context.destination);
      };

      socket.onmessage = (message) => {
        if (!isMountedRef.current) return;
        
        try {
          const data: WebSocketMessage = JSON.parse(message.data);
          
          switch (data.type) {
            case 'cus':
              if (data.transcript) {
                setTranscript(data.transcript);
                const userMessage: ChatMessage = { id: Date.now(), type: 'user', message: data.transcript, timestamp: new Date() };
                setChatMessages(prev => [...prev, userMessage]);
              }
              break;
            case 'llm':
              if (data.response) {
                const botMessage: ChatMessage = { id: Date.now(), type: 'bot', message: data.response, timestamp: new Date() };
                setChatMessages(prev => [...prev, botMessage]);
              }
              break;
            case 'error':
              setError(data.msg || 'Unknown error');
              break;
            case 'close':
              setIsConnected(false);
              console.log('WebSocket closed:', data.msg);
              if (!isReconnectingRef.current) {
                attemptReconnect();
              }
              break;
            case 'end':
              setIsConnected(false);
              console.log('Transcription ended - redirecting to orders');
              window.location.href = '/orderview';
              break;
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      socket.onclose = (event) => {
        if (!isMountedRef.current) return;
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        stopAudioProcessing();
        
        if (event.code !== 1000 && !isReconnectingRef.current) {
          attemptReconnect();
        }
      };

      socket.onerror = (error) => {
        if (!isMountedRef.current) return;
        console.error('WebSocket error:', error);
        setError('WebSocket 連線錯誤');
        setIsConnected(false);
        stopAudioProcessing();
      };

    } catch (err) {
      if (!isMountedRef.current) return;
      console.error('Error initializing audio:', err);
      setError('無法啟用麥克風');
      if (!isReconnectingRef.current) {
        attemptReconnect();
      }
    }
  };

  useEffect(() => {
    isMountedRef.current = true;
    
    loadConversationHistory();
    
    if (!showWelcomePrompt) {
      initializeAudio();
    }

    return () => {
      isMountedRef.current = false;
      isReconnectingRef.current = false;
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (socketRef.current) {
        socketRef.current.close();
      }
      
      stopAudioProcessing();
    };
  }, [showWelcomePrompt]);

  if (isLoading) return <Loading />;

  return (
    <div className="relative flex h-screen flex-col bg-white overflow-hidden">
      <Header to="/choice" name="語音點餐" goto="/orderview" gotoName="前往訂單" />
      {/* Welcome Prompt Modal */}
      {showWelcomePrompt && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl">
            <div className="text-center">
              <div className="w-16 h-16 bg-[#50b4ea] rounded-full flex items-center justify-center mx-auto mb-4">
                <MicIcon />
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">語音點餐系統</h3>
              <p className="text-gray-600 mb-6 leading-relaxed">
                歡迎使用語音點餐！請點擊下方按鈕開始語音點餐，系統將協助您完成點餐流程。
              </p>
              <div className="space-y-3">
                <button
                  onClick={startVoiceOrdering}
                  className="w-full bg-[#50b4ea] text-white py-3 px-6 rounded-xl font-medium hover:bg-blue-600 active:scale-95 transition-all duration-200 shadow-lg"
                >
                  開始語音點餐
                </button>
                <button
                  onClick={() => setShowWelcomePrompt(false)}
                  className="w-full bg-gray-100 text-gray-600 py-3 px-6 rounded-xl font-medium hover:bg-gray-200 active:scale-95 transition-all duration-200"
                >
                  <Link
                    to="/choice"
                  >
                    稍後再說
                  </Link>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Voice Status Indicator - Mobile Optimized */}
      {isConnected && (
        <div className="bg-[#50b4ea] border-b border-blue-200 py-2 px-3 sticky top-[56px] z-20">
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
            <MicIcon />
            <span className="text-white text-xs font-medium">正在聆聽...</span>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 py-2 px-3 sticky top-[56px] z-20">
          <div className="flex items-center justify-center space-x-2">
            <span className="text-red-700 text-xs font-medium">{error}</span>
          </div>
        </div>
      )}

      {/* Main Content: Menu Image */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Image Container with Touch Support */}
        <div 
          ref={containerRef}
          className="flex-1 overflow-hidden bg-gray-100 select-none"
          style={{
            touchAction: 'none'
          }}
        >
          <div className="h-full flex items-center justify-center p-4">
            <img 
              ref={imageRef}
              src={menuImageUrl} 
              alt="菜單"
              className="max-w-full max-h-full rounded-lg shadow-lg border border-gray-300 transition-transform duration-200" 
              style={{
                transform: `scale(${imageScale}) translate(${imagePosition.x}px, ${imagePosition.y}px)`,
                transformOrigin: 'center center',
                cursor: imageScale > 1 ? 'grab' : 'pointer'
              }}
              onTouchStart={handleTouchStart}
              onTouchMove={handleTouchMove}
              onTouchEnd={handleTouchEnd}
              onDoubleClick={handleDoubleClick}
              draggable={false}
            />
          </div>
        </div>

        {/* Mobile Zoom Controls */}
        <div className="bg-white border-t border-gray-200 p-3 shrink-0">
          <div className="flex justify-center space-x-2">
            <button
              onClick={() => setImageScale(Math.min(imageScale + 0.5, 4))}
              className="px-4 py-2 bg-[#50b4ea] text-white rounded-lg text-sm font-medium active:scale-95 transition-transform shadow-md"
            >
              放大 +
            </button>
            <button
              onClick={() => setImageScale(Math.max(imageScale - 0.5, 0.5))}
              className="px-4 py-2 bg-gray-500 text-white rounded-lg text-sm font-medium active:scale-95 transition-transform shadow-md"
            >
              縮小 -
            </button>
            <button
              onClick={resetImagePosition}
              className="px-4 py-2 bg-gray-400 text-white rounded-lg text-sm font-medium active:scale-95 transition-transform shadow-md"
            >
              重置
            </button>
          </div>
          <div className="text-center mt-2">
            <span className="text-gray-600 text-xs">
              縮放比例: {Math.round(imageScale * 100)}% | 雙指縮放 | 雙擊重置
            </span>
          </div>
        </div>
      </div>

      {/* Chat Toggle Button */}
      <button
        onClick={() => setShowChat(true)}
        className="fixed bottom-4 right-4 bg-[#50b4ea] hover:bg-[#4aa3d9] text-white px-4 py-3 rounded-full shadow-lg hover:shadow-xl active:scale-95 transition-all duration-300 z-40"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">對話</span>
        </div>
      </button>

      {/* Full Screen Chat Modal */}
      {showChat && (
        <div className="fixed inset-0 z-50 bg-white">
          <div className="h-full flex flex-col">
            {/* Chat Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-[#50b4ea] text-white">
              <div className="flex items-center gap-3">
                <img src={Logo} alt="Logo" className="w-6 h-6 rounded-lg" />
                <div>
                  <h3 className="text-lg font-bold">點餐助手</h3>
                  <p className="text-blue-100 text-xs">
                    語音點餐服務
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowChat(false)}
                className="text-white hover:bg-white hover:bg-opacity-20 p-2 rounded-lg transition-all duration-200 active:scale-95"
              >
                <CloseIcon />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-50">
              {isLoadingHistory && (
                <div className="flex justify-center items-center py-4">
                  <div className="text-gray-500 text-sm">載入歷史對話中...</div>
                </div>
              )}
              {chatMessages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] px-4 py-3 rounded-2xl shadow-sm ${
                      message.type === 'user'
                        ? 'bg-[#50b4ea] text-white'
                        : 'bg-white text-black border border-gray-200'
                    }`}
                  >
                    {message.type === 'bot' && (
                      <div className="flex items-center mb-2">
                        <img src={Logo} alt="Logo" className="w-5 h-5 rounded-lg" />
                        <span className="text-xs text-gray-600 ml-2 font-semibold">點餐助手</span>
                      </div>
                    )}
                    <p className="text-sm leading-relaxed">{message.message}</p>
                    <p className={`text-xs mt-2 ${message.type === 'user' ? 'text-blue-100 opacity-80' : 'text-gray-500'}`}>
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {transcript && (
              <div className="px-3 py-2 bg-yellow-50 border-t border-yellow-200">
                <p className="text-sm text-yellow-800">
                  <span className="font-medium">正在識別:</span> {transcript}
                </p>
              </div>
            )}

            <div className="p-3 border-t border-gray-200 bg-white">
              <div className="flex items-center justify-center">
                <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-full ${
                  isConnected ? 'bg-[#50b4ea]' : 'bg-gray-400'
                }`}>
                  <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
                  <MicIcon />
                  <p className="text-xs text-white font-medium">
                    {isConnected ? '語音識別已啟動' : '連接中...'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveTranscription;
