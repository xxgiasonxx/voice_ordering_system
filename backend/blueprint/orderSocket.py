from fastapi import APIRouter, WebSocket, Cookie
from fastapi.responses import JSONResponse
from rag.rag_morning_eat import order_real_time
from setup import cus_choice, vectorstore, conn, redis_client
import os
import logging
import json
from dotenv import load_dotenv
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from typing import Dict, Callable, Awaitable, Tuple, Coroutine
from blueprint.token import decrypt_token, verify_token
from datetime import datetime
from google.cloud import speech
import asyncio
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TranscriptHandler = Callable[[Dict], Awaitable[None]]


audioWS = APIRouter()

@audioWS.get('/history')
async def get_conversation_history(ordering_token: str = Cookie(None)):
    """獲取對話歷史"""
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

    # 從 Redis 獲取對話歷史
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

# 對話歷史
conversation_history = []

async def start_google_streaming_asr(transcript_received_handler: TranscriptHandler) -> Tuple[asyncio.Queue, Coroutine]:
    """
    準備 Google ASR 串流，並回傳音訊佇列以及需要被執行的回應處理器協程。
    """
    try:
        audio_queue = asyncio.Queue()
        client = speech.SpeechAsyncClient()
        recognition_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="zh-TW",
            enable_automatic_punctuation=True,
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=recognition_config,
            interim_results=True,
            # 明確設定為連續辨識模式
            single_utterance=False
        )

        async def audio_generator():
            yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
            while True:
                chunk = await audio_queue.get()
                if chunk is None:
                    break
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
                audio_queue.task_done()

        async def response_processor():
            """
            此協程現在會由呼叫者 (websocket_endpoint) 執行，確保錯誤能被捕獲。
            """
            try:
                requests = audio_generator()
                responses = await client.streaming_recognize(requests=requests)
                logger.info("ASR response processor started. Listening for responses from Google...")
                async for response in responses:
                    logger.debug(f"Received raw response from Google: {response}")
                    if not response.results or not response.results[0].alternatives:
                        continue
                    result = response.results[0]
                    transcript = result.alternatives[0].transcript
                    if result.is_final:
                        if transcript:
                            logger.info(f"Google ASR FINAL transcript: '{transcript}'")
                            formatted_result = {"channel": {"alternatives": [{"transcript": transcript}]}}
                            await transcript_received_handler(formatted_result)
                    else:
                        logger.info(f"Google ASR Interim transcript: '{transcript}'")
            finally:
                logger.info("ASR response processor finished.")

        # 回傳佇列和尚未被執行的協程
        return audio_queue, response_processor()
    except Exception as e:
        raise Exception(f'Could not start Google ASR stream: {e}')


async def process_audio(fast_socket: WebSocket, ordering_token: str) -> Tuple[asyncio.Queue, Coroutine]:
    """
    設定 ASR，並回傳音訊佇列以及 Google 回應處理器。
    """
    async def get_transcript(data: Dict) -> None:
        transcript = data['channel']['alternatives'][0]['transcript']
        if transcript:
            # --- 您的核心業務邏輯，無需變動 ---
            logger.info(f"Handler processing final transcript: {transcript}")
            conv = json.loads(redis_client.get(f'{ordering_token}_conversation'))
            try:
                transcript_send = {"type": "cus", "transcript": transcript, "time": datetime.now().isoformat()}
                await fast_socket.send_json(transcript_send)
                conv.append(transcript_send)
            except Exception as e:
                logger.error(f"Error sending transcript: {e}")
                return
            try:
                response, status, order_diff = await call_llm(transcript, ordering_token)
                llm_send = {"type": "llm", "response": response, "time": datetime.now().isoformat()}
                await fast_socket.send_json(llm_send)
                await fast_socket.send_json({"type": "order", "diff": order_diff})
                conv.append(llm_send)
            except Exception as e:
                logger.error(f"Error calling LLM: {e}")
                return
            redis_client.set(f'{ordering_token}_conversation', json.dumps(conv))
            if status:
                end_send = {"type": "end", "msg": "Conversation ended"}
                await fast_socket.send_json(end_send)
                conv.append(end_send)
                redis_client.set(f'{ordering_token}_conversation', json.dumps(conv))
                await fast_socket.close()

    audio_queue, google_response_processor = await start_google_streaming_asr(get_transcript)
    return audio_queue, google_response_processor


@audioWS.websocket("/asr")
async def websocket_endpoint(websocket: WebSocket, ordering_token: str = Cookie(None)):
    await websocket.accept()
    await websocket.send_json({"type": "success", "msg": "WebSocket connection established"})

    audio_queue = None
    try:
        token = decrypt_token(ordering_token)
        token_id = await verify_token(token)
        if not token_id:
            raise Exception("Invalid or expired token")

        audio_queue, google_response_processor = await process_audio(websocket, ordering_token=token_id)

        # --- 全新的任務管理結構 ---
        async def forward_audio_to_queue():
            """從 WebSocket 接收音訊並放入佇列"""
            try:
                while True:
                    data = await websocket.receive_bytes()
                    # *** 關鍵偵錯日誌：檢查音訊內容 ***
                    logger.info(f"Received audio data of length: {len(data)}, first 20 bytes (hex): {data[:20].hex()}")
                    await audio_queue.put(data)
            except Exception as e:
                logger.error(f"Error receiving audio from websocket: {e}")
            finally:
                # 確保如果接收迴圈結束，也發送結束訊號
                if audio_queue:
                    await audio_queue.put(None)
                logger.info("Audio forwarding task finished.")

        # 同時執行兩個任務：一個轉發音訊，一個處理 Google 回應
        await asyncio.gather(
            forward_audio_to_queue(),
            google_response_processor
        )

    except Exception as e:
        logger.error(f"FATAL ERROR in websocket_endpoint: {e}", exc_info=True)
    finally:
        if websocket.client_state.name == "CONNECTED":
            logger.info("Closing WebSocket connection from finally block.")
            await websocket.close()

    
def order_diff_state(order_state: Dict, new_order_state: Dict):
    '''比較兩個訂單狀態，查看是否新增或減少了項目'''
    old_items = order_state.get('items', [])
    new_items = new_order_state.get('items', [])
    
    # 建立舊項目的映射 (使用id作為key)
    old_items_map = {item['id']: item for item in old_items}
    new_items_map = {item['id']: item for item in new_items}
    
    # 找出新增的項目
    added_items = [item for item in new_items if item['id'] not in old_items_map]
    
    # 找出移除的項目
    removed_items = [item for item in old_items if item['id'] not in new_items_map]
    
    # 找出修改的項目 (數量或客製化變更)
    modified_items = []
    for item_id, new_item in new_items_map.items():
        if item_id in old_items_map:
            old_item = old_items_map[item_id]
            if (new_item['quantity'] != old_item['quantity'] or 
                new_item.get('customization') != old_item.get('customization')):
                modified_items.append({
                    'old': old_item,
                    'new': new_item
                })
    
    return {
        'added': added_items,
        'removed': removed_items,
        'modified': modified_items
    }


# 假設的 LLM 呼叫函數（可替換為 Gemini、OpenAI 或本地模型）
async def call_llm(text: str, token: str) -> str:
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

@audioWS.websocket("/asr")
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
        await websocket.close(code=1008)
        return
    try:
        deepgram_socket = await process_audio(websocket, ordering_token=token_id) 

        while True:
            data = await websocket.receive_bytes()
            # logger.info(f"Received audio data of length: {len(data)}")
            await deepgram_socket.send(data)  # Use await for async send
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        await websocket.send_json({"type": "error", "msg": f"Error processing audio"})
        raise Exception(f'Could not process audio: {e}')
    finally:
        # Add finish() call before closing
        if 'deepgram_socket' in locals():
            await deepgram_socket.finish()
        # Only close websocket if it's still open
        if websocket.client_state.name == "CONNECTED":
            await websocket.send_json({"type": "close", "msg": "Closing WebSocket connection"})
            await websocket.close()