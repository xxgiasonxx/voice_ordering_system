import React, { useState, useEffect, useRef, useCallback } from 'react';
import Loading from '@/pages/Loading';
import Header from '@/components/Header';
import { MicIcon } from '@/components/Icon';
import Logo from '@/assets/Logo.png';
import menuPic1 from '@/assets/176172344.jpg';
import menuPic2 from '@/assets/1081376929.jpg';
import { useToken } from '@/contexts/TokenContext';

interface ChatMessage {
  id: number;
  type: 'user' | 'bot';
  message: string;
  timestamp: Date;
}

interface WebSocketMessage {
  type: 'cus' | 'llm' | 'error' | 'close' | 'success' | 'end' | 'order' | 'asr_partial' | 'asr_final';
  transcript?: string;
  response?: string;
  msg?: string;
  text?: string;
  full_text?: string;
}

const float32ToInt16 = (buffer: Float32Array): ArrayBuffer => {
  let l = buffer.length;
  const buf = new Int16Array(l);
  while (l--) buf[l] = Math.min(1, buffer[l]) * 0x7FFF;
  return buf.buffer;
};

export const LiveTranscription: React.FC = () => {
  const { isLoading } = useToken();
  const [transcript, setTranscript] = useState<string>('');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showWelcome, setShowWelcome] = useState(true);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { id: 0, type: 'bot', message: '您好！歡迎使用語音點餐，請看著菜單告訴我您想要什麼餐點！', timestamp: new Date() }
  ]);

  const socketRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const reconnectRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);
  const isRecordingRef = useRef(false);

  const stopProcessing = useCallback(() => {
    if (streamRef.current) { streamRef.current.getTracks().forEach(t => t.stop()); streamRef.current = null; }
    if (processorRef.current) { try { processorRef.current.disconnect(); } catch {} processorRef.current = null; }
    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') { audioCtxRef.current.close(); audioCtxRef.current = null; }
  }, []);

  const startCapture = () => { if (sourceRef.current && processorRef.current && audioCtxRef.current) { isRecordingRef.current = true; setIsRecording(true); sourceRef.current.connect(processorRef.current); processorRef.current.connect(audioCtxRef.current.destination); } };
  const stopCapture = () => { isRecordingRef.current = false; setIsRecording(false); try { processorRef.current?.disconnect(); } catch {} };

  const initAudio = useCallback(async () => {
    try {
      if (socketRef.current) socketRef.current.close();
      stopProcessing();

      const SAMPLE_RATE = 16000;
      const BUFFER_SIZE = 4096;

      const stream = await navigator.mediaDevices.getUserMedia({ audio: { sampleRate: SAMPLE_RATE, channelCount: 1, echoCancellation: true } });
      if (!isMountedRef.current) { stream.getTracks().forEach(t => t.stop()); return; }
      streamRef.current = stream;

      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      const context = new AudioCtx({ sampleRate: SAMPLE_RATE });
      audioCtxRef.current = context;

      const source = context.createMediaStreamSource(stream);
      const processor = context.createScriptProcessor(BUFFER_SIZE, 1, 1);
      sourceRef.current = source;
      processorRef.current = processor;

      const socket = new WebSocket(`ws://localhost:8000/asr`);
      socketRef.current = socket;

      processor.onaudioprocess = (e) => {
        if (socketRef.current?.readyState === WebSocket.OPEN && isRecordingRef.current) {
          socketRef.current.send(float32ToInt16(e.inputBuffer.getChannelData(0)));
        }
      };

      socket.onopen = () => {
        if (!isMountedRef.current) return;
        setIsConnected(true);
        setError(null);
        if (reconnectRef.current) clearTimeout(reconnectRef.current);
      };

      socket.onmessage = (msg) => {
        if (!isMountedRef.current) return;
        try {
          const data: WebSocketMessage = JSON.parse(msg.data);
          switch (data.type) {
            case 'asr_partial':
              setTranscript(data.text || data.full_text ? `🎤 ${data.text || data.full_text}` : '');
              break;
            case 'asr_final':
              setTranscript('');
              break;
            case 'cus':
              if (data.transcript) {
                setTranscript('');
                setChatMessages(prev => [...prev, { id: Date.now(), type: 'user', message: data.transcript!, timestamp: new Date() }]);
              }
              break;
            case 'llm':
              if (data.response) {
                setChatMessages(prev => [...prev, { id: Date.now() + 1, type: 'bot', message: data.response!, timestamp: new Date() }]);
              }
              break;
            case 'error':
              setError(data.msg || '連線錯誤');
              break;
            case 'close':
              setIsConnected(false);
              if (!reconnectRef.current) scheduleReconnect();
              break;
            case 'end':
              setIsConnected(false);
              window.location.href = '/orderview';
              break;
          }
        } catch {}
      };

      socket.onclose = (e) => {
        if (!isMountedRef.current) return;
        setIsConnected(false);
        stopProcessing();
        if (e.code !== 1000 && !reconnectRef.current) scheduleReconnect();
      };

      socket.onerror = () => { if (isMountedRef.current) { setError('連線錯誤'); setIsConnected(false); stopProcessing(); } };
    } catch (err) {
      if (!isMountedRef.current) return;
      setError('無法啟用麥克風');
      if (!reconnectRef.current) scheduleReconnect();
    }
  }, [stopProcessing]);

  const scheduleReconnect = useCallback((retry = 0) => {
    if (!isMountedRef.current || retry >= 5) return;
    reconnectRef.current = setTimeout(async () => {
      reconnectRef.current = null;
      try { await initAudio(); } catch { scheduleReconnect(retry + 1); }
    }, Math.min(1000 * Math.pow(2, retry), 30000));
  }, [initAudio]);

  useEffect(() => {
    isMountedRef.current = true;
    if (!showWelcome) initAudio();
    return () => {
      isMountedRef.current = false;
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      socketRef.current?.close();
      stopProcessing();
    };
  }, [showWelcome, initAudio, stopProcessing]);

  if (isLoading) return <Loading />;

  return (
    <div className="flex flex-col h-screen bg-[#FFFBF5] overflow-hidden">
      <Header to="/choice" name="語音點餐" goto="/orderview" gotoName="前往訂單" />

      {/* Recording Status Bar */}
      {isConnected && (
        <div className="bg-[#F5A623] px-4 py-2.5 flex items-center justify-center gap-2 animate-fade-in shrink-0">
          <div className={`w-2 h-2 rounded-full ${isRecording ? 'bg-red-400 animate-pulse' : 'bg-white/70'}`} />
          <span className="text-white text-sm font-medium">
            {isRecording ? '🔴 錄音中，請說話...' : '麥克風就緒，按住按鈕說話'}
          </span>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2 flex items-center justify-center gap-2 shrink-0">
          <span className="text-red-600 text-sm">{error}</span>
        </div>
      )}

      {/* Main Content: RWD split layout */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        
        {/* Left/Top: Menu Images */}
        <div className="w-full md:w-1/2 h-2/5 md:h-full overflow-y-auto bg-[#FFFBF5]">
          <div className="p-4 space-y-4">
            <h2 className="text-lg font-bold text-[#2D2A26] mb-2">📋 菜單</h2>
            <img src={menuPic1} alt="菜單 1" className="w-full rounded-2xl shadow-lg" />
            <img src={menuPic2} alt="菜單 2" className="w-full rounded-2xl shadow-lg" />
          </div>
        </div>

        {/* Right/Bottom: Voice Controls & Chat */}
        <div className="w-full md:w-1/2 h-3/5 md:h-full bg-white flex flex-col border-l border-[#EDE8E1] overflow-hidden">
          
          {/* Chat Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#FFFBF5]">
            {chatMessages.length === 0 && (
              <div className="flex-1 flex items-center justify-center text-[#9C9690] text-sm h-full">
                歡迎使用語音點餐，請先按住麥克風說話
              </div>
            )}
            {chatMessages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
                <div className={`max-w-[80%] px-4 py-3 rounded-2xl ${
                  msg.type === 'user'
                    ? 'bg-[#F5A623] text-white rounded-br-md'
                    : 'bg-white text-[#2D2A26] border border-[#EDE8E1] rounded-bl-md shadow-sm'
                }`}>
                  {msg.type === 'bot' && (
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <img src={Logo} alt="" className="w-4 h-4 rounded" />
                      <span className="text-xs text-[#9C9690] font-medium">點餐助手</span>
                    </div>
                  )}
                  <p className="text-sm leading-relaxed">{msg.message}</p>
                  <p className={`text-xs mt-1 ${msg.type === 'user' ? 'text-white/60' : 'text-[#9C9690]'}`}>
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Live Transcript */}
          {transcript && (
            <div className="px-4 py-2 bg-yellow-50 border-t border-yellow-100 shrink-0">
              <p className="text-xs text-yellow-700">
                <span className="font-semibold">🎤 辨識中：</span> {transcript}
              </p>
            </div>
          )}

          {/* Mic Controls */}
          <div className="px-4 py-3 border-t border-[#EDE8E1] bg-white shrink-0">
            <div className="flex items-center justify-center gap-4">
              {!isConnected && (
                <button
                  onClick={initAudio}
                  className="px-6 py-2.5 bg-[#F5A623] text-white text-sm font-bold rounded-full hover:bg-[#E8951A] transition-colors shadow-md"
                >
                  開始連線
                </button>
              )}
              {isConnected && (
                <button
                  onMouseDown={e => { e.preventDefault(); startCapture(); }}
                  onMouseUp={e => { e.preventDefault(); stopCapture(); }}
                  onMouseLeave={e => { e.preventDefault(); stopCapture(); }}
                  onTouchStart={e => { e.preventDefault(); startCapture(); }}
                  onTouchEnd={e => { e.preventDefault(); stopCapture(); }}
                  className={`relative w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 active:scale-90 shadow-xl ${
                    isRecording
                      ? 'bg-red-500 scale-105 shadow-red-500/30'
                      : 'bg-gradient-to-br from-[#F5A623] to-[#FF7A00] shadow-[#F5A623]/30'
                  }`}
                >
                  {isRecording && (
                    <>
                      <span className="absolute inset-0 rounded-full bg-red-400 animate-ping opacity-30" />
                      <span className="absolute inset-[-4px] rounded-full border-4 border-red-300 animate-pulse" />
                    </>
                  )}
                  <span className="text-white"><MicIcon /></span>
                </button>
              )}
            </div>
            <p className="text-center mt-2 text-xs text-[#6B6660] font-medium">
              {isRecording ? '放開結束說話' : (isConnected ? '按住麥克風說話' : '點擊「開始連線」開始點餐')}
            </p>
          </div>

        </div>
      </div>

      {/* Welcome Modal */}
      {showWelcome && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-5 bg-[#FFFBF5]">
          <div className="bg-white rounded-3xl p-8 max-w-sm w-full shadow-2xl border border-[#EDE8E1] text-center animate-slide-up">
            <div className="w-20 h-20 bg-gradient-to-br from-[#F5A623] to-[#FF7A00] rounded-3xl flex items-center justify-center mx-auto mb-5 shadow-lg">
              <span className="text-4xl">🎙️</span>
            </div>
            <h2 className="text-2xl font-bold text-[#2D2A26] mb-2">語音點餐</h2>
            <p className="text-[#6B6660] text-sm leading-relaxed mb-8">
              看著上方菜單，用說話的方式點餐。<br />系統會即時辨識並為您完成點餐流程。
            </p>
            <div className="space-y-3">
              <button
                onClick={() => { setShowWelcome(false); }}
                className="w-full py-4 bg-[#F5A623] text-white font-bold rounded-2xl hover:bg-[#E8951A] active:scale-97 transition-all shadow-lg shadow-[#F5A623]/20 text-base"
              >
                開始說話點餐
              </button>
              <button
                onClick={() => window.location.href = '/choice'}
                className="w-full py-3 bg-[#F5F3EF] text-[#6B6660] font-medium rounded-2xl hover:bg-[#EDE8E1] active:scale-97 transition-all text-sm"
              >
                返回主選單
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveTranscription;
