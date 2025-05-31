import React from 'react';
import { TranscriptItem as TranscriptItemType } from '@/interfaces/whisper';

interface TranscriptItemProps {
  item: TranscriptItemType;
}

export const TranscriptItem: React.FC<TranscriptItemProps> = ({ item }) => {
  const baseClasses = "p-3 mb-2 rounded-lg border transition-all duration-200";
  const typeClasses = item.type === 'partial' 
    ? "text-gray-600 bg-gray-50 border-gray-200" 
    : "text-gray-900 bg-white border-gray-300 font-semibold shadow-sm";

  return (
    <div className={`${baseClasses} ${typeClasses}`}>
      <div className="flex justify-between items-start">
        <p className="flex-1">{item.text}</p>
        <span className="text-xs text-gray-500 ml-2 flex-shrink-0">
          {new Date(item.timestamp).toLocaleTimeString()}
        </span>
      </div>
      {item.type === 'partial' && (
        <div className="mt-1">
          <div className="flex items-center">
            <div className="animate-pulse h-1 w-1 bg-blue-500 rounded-full mr-1"></div>
            <span className="text-xs text-blue-500">正在轉錄...</span>
          </div>
        </div>
      )}
    </div>
  );
};