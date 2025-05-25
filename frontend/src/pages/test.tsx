import { useState, useEffect } from 'react';
import UnsupportVoice from '@/pages/UnsupportVoice';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';

const SpeechToText = () => {
    const [transcribedText, setTranscribedText] = useState('');
    const [apiResponse, setApiResponse] = useState('');
    
    const {
        transcript,
        listening,
        resetTranscript,
        browserSupportsSpeechRecognition,
        finalTranscript
    } = useSpeechRecognition();

    // 調用 API 的函數
    const callAPI = async (text: string) => {
        const base: string = import.meta.env.VITE_BACKEND_API_URL;
        try {
            console.log('調用 API，文字內容：', text);
            // 替換為您的實際 API 端點
            const response = await fetch(base + "/", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text }),
            });
            
            const result = await response.json();
            setApiResponse(JSON.stringify(result, null, 2));
        } catch (error) {
            console.error('API 調用失敗：', error);
            setApiResponse('API 調用失敗');
        }
    };

    // 當語音識別完成一段話時調用 API
    useEffect(() => {
        if (finalTranscript.trim()) {
            setTranscribedText(finalTranscript);
            callAPI(finalTranscript);
        }
    }, [finalTranscript]);

    // 檢查瀏覽器支援
    if (!browserSupportsSpeechRecognition) {
        return <UnsupportVoice />;
    }

    // 開始錄音
    const startRecording = () => {
        resetTranscript();
        setApiResponse('');
        SpeechRecognition.startListening({ 
            continuous: true,
            language: 'zh-TW'
        });
    };

    // 停止錄音
    const stopRecording = () => {
        SpeechRecognition.stopListening();
    };

    return (
        <div style={{ padding: '20px', fontFamily: 'Arial' }}>
            <h1>語音轉文字</h1>
            <button
                onClick={listening ? stopRecording : startRecording}
                style={{
                    padding: '10px 20px',
                    fontSize: '16px',
                    marginBottom: '20px',
                    backgroundColor: listening ? '#ff4444' : '#4CAF50',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                }}
            >
                {listening ? '停止錄音' : '開始錄音'}
            </button>
            
            <div>
                <h3>即時文字：</h3>
                <p style={{ border: '1px solid #ccc', padding: '10px', minHeight: '100px', whiteSpace: 'pre-wrap' }}>
                    {transcript || '尚未轉錄任何內容'}
                </p>
            </div>

            <div>
                <h3>最終識別結果：</h3>
                <p style={{ border: '1px solid #ccc', padding: '10px', minHeight: '50px', whiteSpace: 'pre-wrap' }}>
                    {transcribedText || '尚無完整語音'}
                </p>
            </div>

            <div>
                <h3>API 回應：</h3>
                <pre style={{ border: '1px solid #ccc', padding: '10px', minHeight: '100px', backgroundColor: '#f5f5f5' }}>
                    {apiResponse || '尚無 API 回應'}
                </pre>
            </div>
        </div>
    );
};

export default SpeechToText;