"""
Streaming ASR via WebSocket + Qwen3-ASR (qwen-asr library)
- Sliding Window Audio Buffer (2.0s window, 0.5s overlap)
- Qwen3-ASR via qwen-asr library (CPU)
- WebSocket for audio upload + real-time results (asr_partial / asr_final / llm)
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Cookie
from fastapi.responses import JSONResponse
from typing import Optional
import asyncio
import json
import logging
import tempfile
import os
from dataclasses import dataclass, field
from datetime import datetime
from dotenv import load_dotenv
import os as os_mod

from rag.rag_morning_eat import order_real_time
from setup import cus_choice, vectorstore, conn, redis_client
from blueprint.token import decrypt_token, verify_token

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QWEN_ASR_MODEL = os_mod.getenv("QWEN_ASR_MODEL", "Qwen/Qwen3-ASR-0.6B")
SAMPLE_RATE = 16000
WINDOW_SIZE = 2.0
OVERLAP = 0.5
BYTES_PER_SECOND = SAMPLE_RATE * 2
MAX_BUFFER_SIZE = 10 * BYTES_PER_SECOND

audioSSE = APIRouter()

# Lazy-loaded ASR model
_asr_model = None


def get_asr_model():
    """Lazy init Qwen3-ASR model via qwen-asr library (CPU)"""
    global _asr_model
    if _asr_model is None:
        import torch
        from qwen_asr import Qwen3ASRModel

        logger.info(f"Loading Qwen3-ASR model: {QWEN_ASR_MODEL}")

        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        device = "cuda:0" if torch.cuda.is_available() else "cpu"

        _asr_model = Qwen3ASRModel.from_pretrained(
            QWEN_ASR_MODEL,
            dtype=dtype,
            device_map=device,
            max_inference_batch_size=32,
            max_new_tokens=256,
        )

        logger.info("ASR model loaded successfully")
    return _asr_model


@dataclass
class AudioBuffer:
    window_size: float = WINDOW_SIZE
    overlap: float = OVERLAP
    sample_rate: int = SAMPLE_RATE
    buffer: bytearray = field(default_factory=bytearray)
    last_final_text: str = ""
    pending_text: str = ""

    def __post_init__(self):
        self.bytes_per_second = self.sample_rate * 2
        self.window_bytes = int(self.bytes_per_second * self.window_size)
        self.overlap_bytes = int(self.bytes_per_second * self.overlap)

    def add_chunk(self, chunk: bytes) -> Optional[bytes]:
        self.buffer.extend(chunk)
        if len(self.buffer) >= self.window_bytes:
            result = bytes(self.buffer)
            self.buffer = self.buffer[-self.overlap_bytes:]
            return result
        return None

    def extract_new_part(self, current_text: str) -> str:
        if not current_text:
            return ""
        if self.last_final_text and current_text.startswith(self.last_final_text):
            return current_text[len(self.last_final_text):].strip()
        if self.last_final_text in current_text:
            idx = current_text.index(self.last_final_text) + len(self.last_final_text)
            return current_text[idx:].strip()
        return current_text.strip()

    def update_final(self, text: str):
        self.last_final_text = text
        self.pending_text = ""

    def flush_remaining(self) -> Optional[bytes]:
        if len(self.buffer) > 0:
            result = bytes(self.buffer)
            self.buffer = bytearray()
            return result
        return None


async def transcribe_with_qwen(audio_bytes: bytes) -> str:
    """Transcribe audio using local Qwen3-ASR model (qwen-asr, CPU)"""
    import numpy as np
    import soundfile as sf

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        temp_path = f.name

    try:
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        sf.write(temp_path, audio_array, SAMPLE_RATE)

        model = get_asr_model()
        results = model.transcribe(audio=temp_path, language="Chinese")
        return results[0].text
    except Exception as e:
        logger.error(f"Qwen ASR local inference failed: {e}")
        raise
    finally:
        os.remove(temp_path)


def order_diff_state(order_state: dict, new_order_state: dict):
    old_items = order_state.get('items', [])
    new_items = new_order_state.get('items', [])
    old_items_map = {item['id']: item for item in old_items}
    new_items_map = {item['id']: item for item in new_items}

    added_items = [item for item in new_items if item['id'] not in old_items_map]
    removed_items = [item for item in old_items if item['id'] not in new_items_map]

    modified_items = []
    for item_id, new_item in new_items_map.items():
        if item_id in old_items_map:
            old_item = old_items_map[item_id]
            if (new_item['quantity'] != old_item['quantity'] or
                    new_item.get('customization') != old_item.get('customization')):
                modified_items.append({'old': old_item, 'new': new_item})

    return {
        'added': added_items,
        'removed': removed_items,
        'modified': modified_items
    }


async def call_llm(text: str, token: str):
    order_state = json.loads(redis_client.get(f'{token}_order_state'))
    new_order_state = {
        "items": order_state.get('items', []),
        "total_price": order_state.get('total_price', 0),
        "status": order_state.get('status', 'start'),
    }
    conv_history = json.loads(redis_client.get(f'{token}_conversation'))

    response, neww_order_state = order_real_time(
        query=text,
        conversation_history=conv_history,
        vectorstore=vectorstore,
        cus_choice=cus_choice,
        order_state=new_order_state,
        conn=conn
    )
    order_diff = order_diff_state(new_order_state, neww_order_state)
    order_state.update(new_order_state)
    redis_client.set(f'{token}_order_state', json.dumps(order_state))
    return response, order_state.get('status', '') == 'end', order_diff


@audioSSE.get('/history')
async def get_conversation_history(ordering_token: str = Cookie(None)):
    try:
        token = decrypt_token(ordering_token)
        token_id = await verify_token(token)
        if not token_id:
            raise Exception("Invalid or expired token")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return JSONResponse(
            content={"error": "Invalid or expired token"},
            status_code=401
        )

    conversation_history = redis_client.get(f'{token_id}_conversation')
    if conversation_history:
        return JSONResponse(
            content={"conversation": json.loads(conversation_history)},
            status_code=200
        )
    else:
        return JSONResponse(
            content={"message": "No conversation history found"},
            status_code=404
        )


async def process_window(websocket: WebSocket, audio_data: bytes, audio_buffer: AudioBuffer, ordering_token: str):
    try:
        logger.info(f"Processing window of {len(audio_data)} bytes")
        transcript = await transcribe_with_qwen(audio_data)

        if not transcript:
            return

        new_text = audio_buffer.extract_new_part(transcript)

        if new_text:
            await websocket.send_json({
                "type": "asr_partial",
                "text": new_text,
                "full_text": transcript,
                "final": False
            })
            audio_buffer.pending_text += new_text
        else:
            await websocket.send_json({
                "type": "asr_partial",
                "text": "",
                "full_text": transcript,
                "final": False
            })

        await websocket.send_json({
            "type": "asr_final",
            "text": transcript,
            "new_part": new_text,
            "final": True
        })

        audio_buffer.update_final(transcript)

        if new_text:
            conv = json.loads(redis_client.get(f'{ordering_token}_conversation'))
            try:
                transcript_send = {"type": "cus", "transcript": new_text, "time": datetime.now().isoformat()}
                await websocket.send_json(transcript_send)
                conv.append(transcript_send)
            except Exception as e:
                logger.error(f"Error sending transcript: {e}")
                return
            try:
                response, status, order_diff = await call_llm(new_text, ordering_token)
                llm_send = {"type": "llm", "response": response, "time": datetime.now().isoformat()}
                await websocket.send_json(llm_send)
                await websocket.send_json({"type": "order", "diff": order_diff})
                conv.append(llm_send)
            except Exception as e:
                logger.error(f"Error calling LLM: {e}")
                return
            redis_client.set(f'{ordering_token}_conversation', json.dumps(conv))
            if status:
                end_send = {"type": "end", "msg": "Conversation ended"}
                await websocket.send_json(end_send)
                conv.append(end_send)
                redis_client.set(f'{ordering_token}_conversation', json.dumps(conv))
                await websocket.close()

    except Exception as e:
        logger.error(f"Window processing error: {e}")
        await websocket.send_json({"type": "error", "msg": f"ASR processing error: {str(e)}"})


@audioSSE.websocket("/asr")
async def websocket_endpoint(websocket: WebSocket, ordering_token: str = Cookie(None)):
    await websocket.accept()
    await websocket.send_json({"type": "success", "msg": "WebSocket connection established"})

    try:
        token = decrypt_token(ordering_token)
        token_id = await verify_token(token)
        if not token_id:
            await websocket.send_json({"type": "error", "msg": "Invalid or expired token"})
            await websocket.close(code=1008)
            raise Exception("Invalid or expired token")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        await websocket.send_json({"type": "close", "msg": "Token verification failed"})
        if websocket.client_state.name == "CONNECTED":
            await websocket.close(code=1008)
        return

    audio_buffer = AudioBuffer(window_size=WINDOW_SIZE, overlap=OVERLAP)

    try:
        while True:
            data = await websocket.receive_bytes()
            logger.debug(f"Received audio chunk of {len(data)} bytes")

            if len(audio_buffer.buffer) + len(data) > MAX_BUFFER_SIZE:
                logger.warning("Buffer overflow, flushing...")
                audio_buffer.buffer = audio_buffer.buffer[-MAX_BUFFER_SIZE // 2:]

            full_window = audio_buffer.add_chunk(data)

            if full_window:
                await process_window(websocket, full_window, audio_buffer, token_id)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error processing audio: {e}", exc_info=True)
        if websocket.client_state.name == "CONNECTED":
            await websocket.send_json({"type": "error", "msg": "Error processing audio"})
    finally:
        remaining = audio_buffer.flush_remaining()
        if remaining and len(remaining) > BYTES_PER_SECOND:
            try:
                await process_window(websocket, remaining, audio_buffer, token_id)
            except Exception:
                pass
        if websocket.client_state.name == "CONNECTED":
            await websocket.send_json({"type": "close", "msg": "Closing WebSocket connection"})
            await websocket.close()
