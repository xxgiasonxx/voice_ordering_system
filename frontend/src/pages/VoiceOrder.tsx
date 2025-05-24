import { Link } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import menuImageUrl from "../assets/176172344.jpg"
import icon from '@/assets/icon.png';

const ArrowLeftIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256" {...props}>
        <path d="M224,128a8,8,0,0,1-8,8H59.31l58.35,58.34a8,8,0,0,1-11.32,11.32l-72-72a8,8,0,0,1,0-11.32l72-72a8,8,0,0,1,11.32,11.32L59.31,120H216A8,8,0,0,1,224,128Z"></path>
    </svg>
);

const SendIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor"/>
    </svg>
);

const CloseIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
);

const MicIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2Z" fill="currentColor"/>
        <path d="M19 11C19 15.42 15.42 19 11 19V21H13V23H11H9V21H11V19C6.58 19 3 15.42 3 11H5C5 14.31 7.69 17 11 17C14.31 17 17 14.31 17 11H19Z" fill="currentColor"/>
    </svg>
);

interface ChatMessage {
    id: number;
    type: 'user' | 'bot';
    message: string;
    timestamp: Date;
}

function VoiceOrderScreen() {
    const [isListening, setIsListening] = useState(false);
    const [inputText, setInputText] = useState('');
    const [showChat, setShowChat] = useState(false);
    const [imageScale, setImageScale] = useState(1);
    const [imagePosition, setImagePosition] = useState({ x: 0, y: 0 });
    const imageRef = useRef<HTMLImageElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
        {
            id: 1,
            type: 'bot',
            message: '您好！歡迎使用語音點餐系統，請參考上方菜單並告訴我您想要什麼餐點？',
            timestamp: new Date()
        }
    ]);

    useEffect(() => {
        setIsListening(true);
    }, []);

    const handleSendMessage = () => {
        if (inputText.trim()) {
            const userMessage: ChatMessage = {
                id: chatMessages.length + 1,
                type: 'user',
                message: inputText,
                timestamp: new Date()
            };

            const botResponseMessage = `感謝您的訊息：「${inputText}」。我們正在處理您的點餐。`;

            const botResponse: ChatMessage = {
                id: chatMessages.length + 2,
                type: 'bot',
                message: botResponseMessage,
                timestamp: new Date()
            };

            setChatMessages(prevMessages => [...prevMessages, userMessage, botResponse]);
            setInputText('');
        }
    };

    const resetImagePosition = () => {
        setImageScale(1);
        setImagePosition({ x: 0, y: 0 });
    };

    const handleImagePinch = (e: React.TouchEvent) => {
        if (e.touches.length === 2) {
            e.preventDefault();
            // 簡單的捏合縮放邏輯
            // 這裡可以根據需要實現更複雜的縮放邏輯
        }
    };

    return (
        <div className="relative flex h-screen flex-col bg-white overflow-hidden">
            {/* Header - Mobile Optimized */}
            <div className="flex items-center bg-white px-3 py-2 justify-between sticky top-0 z-30 shadow-sm border-b border-gray-200 min-h-[56px]">
                <div className="text-black flex size-10 shrink-0 items-center justify-center rounded-full hover:bg-gray-100 transition-colors">
                    <Link to="/choice">
                        <ArrowLeftIcon />
                    </Link>
                </div>
                <h2 className="text-black text-lg font-bold tracking-tight flex-1 text-center pr-10">語音點餐助手</h2>
            </div>

            {/* Voice Status Indicator - Mobile Optimized */}
            {isListening && (
                <div className="bg-[#50b4ea] border-b border-blue-200 py-2 px-3 sticky top-[56px] z-20">
                    <div className="flex items-center justify-center space-x-2">
                        <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                        <MicIcon />
                        <span className="text-white text-xs font-medium">正在聆聽...</span>
                    </div>
                </div>
            )}

            {/* Main Content: Menu Image - Mobile Optimized */}
            <div className="flex-1 overflow-hidden">
                <div className="h-full flex flex-col">
                    <h3 className="text-xl font-bold py-3 text-black text-center bg-white border-b border-gray-200">菜單</h3>
                    
                    {/* Image Container with improved mobile viewing */}
                    <div 
                        ref={containerRef}
                        className="flex-1 overflow-auto bg-gray-100"
                        style={{ 
                            touchAction: imageScale > 1 ? 'pan-x pan-y' : 'auto',
                            overflowX: imageScale > 1 ? 'auto' : 'hidden',
                            overflowY: 'auto'
                        }}
                    >
                        <div className="min-h-full flex items-start justify-center p-2">
                            <img 
                                ref={imageRef}
                                src={menuImageUrl} 
                                alt="菜單" 
                                className="w-full max-w-none rounded-lg shadow-lg border border-gray-300 transition-transform duration-300" 
                                style={{
                                    transform: `scale(${imageScale}) translate(${imagePosition.x}px, ${imagePosition.y}px)`,
                                    transformOrigin: 'center top',
                                    minHeight: imageScale > 1 ? 'auto' : '100%',
                                    objectFit: 'contain'
                                }}
                                onTouchStart={handleImagePinch}
                                onTouchMove={handleImagePinch}
                            />
                        </div>
                    </div>
                    
                    {/* Fixed Mobile Zoom Controls */}
                    <div className="bg-white border-t border-gray-200 p-3">
                        <div className="flex justify-center space-x-2">
                            <button
                                onClick={() => setImageScale(Math.min(imageScale + 0.5, 3))}
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
                            <span className="text-xs text-gray-600">縮放比例: {Math.round(imageScale * 100)}%</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Chat Toggle Button - Mobile Optimized */}
            <button
                onClick={() => setShowChat(true)}
                className="fixed bottom-4 right-4 bg-[#50b4ea] hover:bg-[#4aa3d9] text-white px-4 py-3 rounded-full shadow-lg hover:shadow-xl active:scale-95 transition-all duration-300 z-40"
            >
                <div className="flex items-center gap-2">
                    <span className="text-lg">💬</span>
                    <span className="text-sm font-medium">對話</span>
                </div>
            </button>

            {/* Full Screen Mobile Chat Overlay */}
            {showChat && (
                <div className="fixed inset-0 z-50 bg-white">
                    {/* Mobile Chat Container */}
                    <div className="h-full flex flex-col">
                        {/* Chat Header - Mobile */}
                        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-[#50b4ea] text-white">
                            <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 bg-white bg-opacity-20 rounded-xl flex items-center justify-center">
                                    <img src={icon} alt="Logo" className="w-6 h-6 rounded-lg" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold">點餐助手</h3>
                                    <p className="text-blue-100 text-xs">智能語音點餐</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setShowChat(false)}
                                className="text-white hover:bg-white hover:bg-opacity-20 p-2 rounded-lg transition-all duration-200 active:scale-95"
                            >
                                <CloseIcon />
                            </button>
                        </div>

                        {/* Chat Messages - Mobile Optimized */}
                        <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-50">
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
                                                <img src={icon} alt="Logo" className="w-5 h-5 rounded-lg" />
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

                        {/* Chat Input - Mobile Optimized */}
                        <div className="p-3 border-t border-gray-200 bg-white">
                            <div className="flex items-center space-x-2 mb-2">
                                <input
                                    type="text"
                                    value={inputText}
                                    onChange={(e) => setInputText(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                                    placeholder="說話或輸入餐點..."
                                    className="flex-1 px-4 py-3 border border-gray-300 rounded-2xl focus:outline-none focus:ring-2 focus:ring-[#50b4ea] focus:border-transparent text-sm transition-all duration-200"
                                />
                                <button
                                    onClick={handleSendMessage}
                                    disabled={!inputText.trim()}
                                    className="flex items-center justify-center w-12 h-12 bg-[#50b4ea] text-white rounded-2xl active:scale-95 transition-all duration-200 shadow-lg disabled:bg-gray-400 disabled:cursor-not-allowed"
                                >
                                    <SendIcon />
                                </button>
                            </div>
                            {/* Voice Status - Mobile */}
                            <div className="flex items-center justify-center">
                                <div className="flex items-center space-x-2 bg-[#50b4ea] px-3 py-1.5 rounded-full">
                                    <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
                                    <MicIcon />
                                    <p className="text-xs text-white font-medium">語音識別已啟動</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default VoiceOrderScreen;
