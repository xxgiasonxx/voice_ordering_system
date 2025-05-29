import React, { useRef } from "react";
import WaveSurfer from "wavesurfer.js";
import { useVoiceOrder } from "@/hooks/useVoiceOrder";

const VoiceOrder: React.FC = () => {
  const waveSurferRef = useRef<WaveSurfer | null>(null);
  const waveformRef = useRef<HTMLDivElement>(null);
  const { isRecording, transcript, response, isSpeaking, startListening, stopListening } =
    useVoiceOrder(waveSurferRef);

  React.useEffect(() => {
    if (waveformRef.current && !waveSurferRef.current) {
      waveSurferRef.current = WaveSurfer.create({
        container: waveformRef.current,
        waveColor: "#4F4A85",
        progressColor: "#383351",
        height: 100,
      });
    }
    return () => {
      waveSurferRef.current?.destroy();
    };
  }, []);

  return (
    <div className="p-4 max-w-md mx-auto bg-white rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-4">語音點餐系統</h1>
      <div ref={waveformRef} className="mb-4" />
      <div className="mb-4">
        <p className="text-lg">
          <strong>語音輸入：</strong> {transcript || "等待語音..."}
        </p>
        <p className="text-lg">
          <strong>回應：</strong> {response || "等待回應..."}
        </p>
      </div>
      <div className="flex space-x-4">
        <button
          onClick={startListening}
          disabled={isRecording}
          className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-400"
        >
          開始錄音
        </button>
        <button
          onClick={stopListening}
          disabled={!isRecording}
          className="px-4 py-2 bg-red-500 text-white rounded disabled:bg-gray-400"
        >
          停止錄音
        </button>
      </div>
      {isSpeaking && <p className="mt-2 text-green-500">正在播放回應...</p>}
    </div>
  );
};

export default VoiceOrder;