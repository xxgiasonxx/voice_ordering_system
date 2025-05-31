export interface TranscriptMessage {
  type: 'status' | 'partial_transcript' | 'final_transcript';
  message?: string;
  start_time?: number;
  end_time?: number;
  text?: string;
  is_final?: boolean;
}

export interface TranscriptItem {
  id: string;
  text: string;
  type: 'partial' | 'final';
  timestamp: number;
}

export interface AudioConfig {
  sampleRate: number;
  channelCount: number;
  echoCancellation: boolean;
  noiseSuppression: boolean;
}