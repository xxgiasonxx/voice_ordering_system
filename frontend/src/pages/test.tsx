import { useState, useRef } from 'react';
import axios from 'axios';

const AudioRecorder = () => {
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState('');
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const hasDetectedMeaningfulAudioRef = useRef(false); // Added ref

    const RMS_SILENCE_THRESHOLD = 0.01;
    const SILENCE_DURATION = 1000;

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = new MediaRecorder(stream);
            audioChunksRef.current = [];
            hasDetectedMeaningfulAudioRef.current = false; // Reset flag

            audioContextRef.current = new AudioContext();
            const source = audioContextRef.current.createMediaStreamSource(stream);
            analyserRef.current = audioContextRef.current.createAnalyser();
            analyserRef.current.fftSize = 2048;
            source.connect(analyserRef.current);

            mediaRecorderRef.current.ondataavailable = (event: BlobEvent) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorderRef.current.onstop = () => {
                setIsRecording(false);

                const shouldSend = audioChunksRef.current.length > 0 && hasDetectedMeaningfulAudioRef.current;

                if (shouldSend) {
                    sendAudioToBackend();
                } else {
                    if (audioChunksRef.current.length > 0 && !hasDetectedMeaningfulAudioRef.current) {
                        console.log("錄音已停止，但未偵測到有效語音。不會傳送資料。");
                        // Optionally set a message for the user if no meaningful audio was detected but some (silent) data exists
                        // setTranscript("未偵測到有效語音，請重試。");
                    } else if (audioChunksRef.current.length === 0) {
                        console.log("錄音已停止，沒有收集到音訊資料。");
                    }
                    audioChunksRef.current = []; // Clear chunks if not sending
                }

                // 清理資源
                if (mediaRecorderRef.current) {
                    mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
                }
                if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
                    audioContextRef.current.close().then(() => {
                        audioContextRef.current = null;
                        analyserRef.current = null;
                    }).catch(e => console.error("Error closing AudioContext:", e));
                } else {
                    audioContextRef.current = null;
                    analyserRef.current = null;
                }
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);
            detectSilence();
        } catch (err) {
            console.error("開始錄音失敗:", err);
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.stop();
        }
    };

    const detectSilence = () => {
        if (!analyserRef.current || !audioContextRef.current) {
            console.warn("Analyser 或 AudioContext 未初始化，無法偵測停頓。");
            return;
        }

        const bufferLength = analyserRef.current.fftSize;
        const dataArray = new Uint8Array(bufferLength);
        let silenceStartTimestamp: number | null = null;

        const check = () => {
            if (mediaRecorderRef.current?.state !== 'recording' || !analyserRef.current) {
                return;
            }

            analyserRef.current.getByteTimeDomainData(dataArray);

            let sumOfSquares = 0.0;
            for (let i = 0; i < bufferLength; i++) {
                const normalizedSample = (dataArray[i] / 128.0) - 1.0;
                sumOfSquares += normalizedSample * normalizedSample;
            }
            const rms = Math.sqrt(sumOfSquares / bufferLength);

            if (rms < RMS_SILENCE_THRESHOLD) {
                if (silenceStartTimestamp === null) {
                    silenceStartTimestamp = Date.now();
                } else {
                    if (Date.now() - silenceStartTimestamp >= SILENCE_DURATION) {
                        if (mediaRecorderRef.current?.state === 'recording') {
                            console.log(`偵測到持續停頓 ${SILENCE_DURATION}ms. RMS: ${rms.toFixed(4)}. 停止錄音。`);
                            mediaRecorderRef.current.stop();
                        }
                        return;
                    }
                }
            } else {
                hasDetectedMeaningfulAudioRef.current = true; // Sound detected
                silenceStartTimestamp = null;
            }

            if (mediaRecorderRef.current?.state === 'recording') {
                requestAnimationFrame(check);
            }
        };

        requestAnimationFrame(check);
    };

    const sendAudioToBackend = async () => {
        if (audioChunksRef.current.length === 0) return;

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');

        try {
            const response = await axios.post('http://localhost:8000/transcribe', formData);
            setTranscript(response.data.transcript);
        } catch (err) {
            console.error('傳送音訊失敗:', err);
            setTranscript('轉錄失敗，請稍後再試。');
        } finally {
            audioChunksRef.current = [];
        }
    };

    return (
        <div>
            <h1>語音錄製器</h1>
            <button onClick={isRecording ? stopRecording : startRecording} disabled={!navigator.mediaDevices}>
                {isRecording ? '停止錄音' : '開始錄音'}
            </button>
            {!navigator.mediaDevices && <p style={{color: 'red'}}>您的瀏覽器不支援錄音功能或未授予麥克風權限。</p>}
            {transcript && <p>轉錄結果: {transcript}</p>}
        </div>
    );
};

export default AudioRecorder;