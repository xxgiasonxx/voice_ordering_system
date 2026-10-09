"""
Streaming ASR via WebSocket + Moonshine (transformers)
- 按住說話：放開按鈕時前端送 end_utterance，整段語音辨識一次、呼叫 LLM 一次
- 說話途中每 2 秒辨識一次目前內容，只用來即時顯示
- moonshine-ai/moonshine-streaming-tiny-zh via transformers (CPU)
- WebSocket for audio upload + real-time results (asr_partial / asr_final / llm)
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Cookie
from fastapi.responses import JSONResponse
import asyncio
import json
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from opencc import OpenCC
import os as os_mod

from rag.rag_morning_eat import order_real_time
from setup import cus_choice, vectorstore, conn, redis_client
from blueprint.token import decrypt_token, verify_token

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ASR_MODEL = os_mod.getenv("ASR_MODEL", "moonshine-ai/moonshine-streaming-tiny-zh")
SAMPLE_RATE = 16000
BYTES_PER_SECOND = SAMPLE_RATE * 2
PARTIAL_BYTES = 2 * BYTES_PER_SECOND        # 每多 2 秒更新一次即時字幕
MIN_UTTERANCE_BYTES = BYTES_PER_SECOND // 3  # 不到 0.33 秒視為誤觸
MAX_BUFFER_SIZE = 30 * BYTES_PER_SECOND

audioSSE = APIRouter()

# Moonshine 輸出簡體中文，轉成台灣繁體
_s2tw = OpenCC("s2tw")

# Lazy-loaded ASR model
_asr_model = None


def get_asr_model():
    """Lazy init Moonshine streaming ASR model + processor (CPU)"""
    global _asr_model
    if _asr_model is None:
        from transformers import MoonshineStreamingForConditionalGeneration, AutoProcessor

        logger.info(f"Loading Moonshine ASR model: {ASR_MODEL}")

        model = MoonshineStreamingForConditionalGeneration.from_pretrained(ASR_MODEL).eval()
        processor = AutoProcessor.from_pretrained(ASR_MODEL)
        _asr_model = (model, processor)

        logger.info("ASR model loaded successfully")
    return _asr_model


async def transcribe_with_moonshine(audio_bytes: bytes) -> str:
    """Transcribe audio using local Moonshine streaming model (CPU)"""
    # 推論是同步運算，丟到 thread 避免卡住 event loop
    return await asyncio.to_thread(_transcribe_sync, audio_bytes)


def _transcribe_sync(audio_bytes: bytes) -> str:
    import numpy as np
    import torch

    try:
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        model, processor = get_asr_model()
        inputs = processor(audio_array, return_tensors="pt", sampling_rate=SAMPLE_RATE)
        # Moonshine 建議：依音訊長度限制 token 數，避免幻覺重複輸出
        seq_lens = inputs.attention_mask.sum(dim=-1)
        max_new_tokens = int((seq_lens * 6.5 / SAMPLE_RATE).max().item()) + 2
        with torch.inference_mode():
            generated = model.generate(**inputs, max_new_tokens=max_new_tokens)
        return _s2tw.convert(processor.batch_decode(generated, skip_special_tokens=True)[0]).replace("臺", "台")
    except Exception as e:
        logger.error(f"Moonshine ASR local inference failed: {e}")
        raise


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

    # LLM 呼叫是同步的（Docker 裡 CPU 跑可能要數十秒），丟到 thread 避免整個 WebSocket 卡死
    response, neww_order_state = await asyncio.to_thread(
        order_real_time,
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


async def send_partial(websocket: WebSocket, audio_data: bytes):
    """說話途中的即時字幕，只顯示不呼叫 LLM"""
    transcript = await transcribe_with_moonshine(audio_data)
    if transcript:
        await websocket.send_json({"type": "asr_partial", "text": transcript, "full_text": transcript, "final": False})


async def process_utterance(websocket: WebSocket, audio_data: bytes, ordering_token: str):
    """放開按鈕後：整段語音辨識一次，再呼叫 LLM 一次"""
    try:
        import numpy as np
        transcript = await transcribe_with_moonshine(audio_data)
        # 音量峰值（0~1）：接近 0 代表瀏覽器沒收到聲音（麥克風權限或裝置問題）
        peak = int(np.abs(np.frombuffer(audio_data, dtype=np.int16)).max()) / 32768
        logger.info(f"ASR ({len(audio_data) / BYTES_PER_SECOND:.1f}s, peak={peak:.3f}): {transcript!r}")
        await websocket.send_json({"type": "asr_final", "text": transcript, "new_part": transcript, "final": True})

        if not transcript:
            reply = "沒有收到聲音耶，請確認麥克風有開、瀏覽器有麥克風權限喔！" if peak < 0.02 else "不好意思，沒聽清楚，可以再說一次嗎？"
            await websocket.send_json({"type": "llm", "response": reply, "time": datetime.now().isoformat()})
            return

        conv = json.loads(redis_client.get(f'{ordering_token}_conversation'))
        transcript_send = {"type": "cus", "transcript": transcript, "time": datetime.now().isoformat()}
        await websocket.send_json(transcript_send)
        conv.append(transcript_send)
        try:
            start = time.time()
            response, status, order_diff = await call_llm(transcript, ordering_token)
            logger.info(f"LLM ({time.time() - start:.1f}s): {response!r}")
            llm_send = {"type": "llm", "response": response, "time": datetime.now().isoformat()}
            await websocket.send_json(llm_send)
            await websocket.send_json({"type": "order", "diff": order_diff})
            conv.append(llm_send)
        except Exception as e:
            logger.error(f"Error calling LLM: {e}", exc_info=True)
            await websocket.send_json({"type": "error", "msg": "點餐系統暫時出錯，請再說一次"})
            return
        redis_client.set(f'{ordering_token}_conversation', json.dumps(conv))
        if status:
            end_send = {"type": "end", "msg": "Conversation ended"}
            await websocket.send_json(end_send)
            conv.append(end_send)
            redis_client.set(f'{ordering_token}_conversation', json.dumps(conv))
            await websocket.close()

    except Exception as e:
        logger.error(f"Utterance processing error: {e}", exc_info=True)
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

    utterance = bytearray()
    last_partial = 0

    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                raise WebSocketDisconnect(message.get("code", 1000))

            if message.get("bytes"):
                if len(utterance) + len(message["bytes"]) > MAX_BUFFER_SIZE:
                    logger.warning("Utterance too long, dropping oldest audio")
                    utterance = utterance[-MAX_BUFFER_SIZE // 2:]
                    last_partial = 0
                utterance.extend(message["bytes"])
                if len(utterance) - last_partial >= PARTIAL_BYTES:
                    last_partial = len(utterance)
                    await send_partial(websocket, bytes(utterance))

            elif message.get("text"):
                try:
                    signal = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue
                # 前端放開按鈕：處理整段語音
                if signal.get("type") == "end_utterance":
                    audio_data, utterance, last_partial = bytes(utterance), bytearray(), 0
                    if len(audio_data) >= MIN_UTTERANCE_BYTES:
                        await process_utterance(websocket, audio_data, token_id)
                        if websocket.application_state.name != "CONNECTED":
                            break  # 訂單結束，process_utterance 已關閉連線

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error processing audio: {e}", exc_info=True)
        if websocket.client_state.name == "CONNECTED":
            await websocket.send_json({"type": "error", "msg": "Error processing audio"})
    finally:
        if websocket.client_state.name == "CONNECTED":
            await websocket.send_json({"type": "close", "msg": "Closing WebSocket connection"})
            await websocket.close()
