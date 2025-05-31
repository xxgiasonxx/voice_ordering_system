import React from 'react';

interface StatusIndicatorProps {
  status: string;
  isConnected: boolean;
  isRecording: boolean;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ 
  status, 
  isConnected, 
  isRecording 
}) => {
  const getStatusColor = () => {
    if (!isConnected) return 'text-red-500';
    if (isRecording) return 'text-green-500';
    return 'text-blue-500';
  };

  const getStatusIcon = () => {
    if (!isConnected) {
      return (
        <div className="w-2 h-2 bg-red-500 rounded-full"></div>
      );
    }
    if (isRecording) {
      return (
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
      );
    }
    return (
      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
    );
  };

  return (
    <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
      {getStatusIcon()}
      <span className={`text-sm font-medium ${getStatusColor()}`}>
        {status}
      </span>
    </div>
  );
};