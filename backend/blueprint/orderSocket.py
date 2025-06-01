from fastapi import APIRouter, WebSocket, Cookie
from rag.rag_morning_eat import order_real_time
from setup import cus_choice, vectorstore, conn, redis_client
import os
import logging
import json
from dotenv import load_dotenv
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from typing import Dict, Callable
from blueprint.token import decrypt_token, verify_token
from datetime import datetime
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

audioWS = APIRouter()

# 對話歷史
conversation_history = []

dg_client = DeepgramClient(os.getenv('DEEPGRAM_API_KEY'))

async def process_audio(fast_socket: WebSocket, ordering_token: str):
    async def get_transcript(data: Dict) -> None:
        if 'channel' in data:
            transcript = data['channel']['alternatives'][0]['transcript']
            if transcript:
                logger.info(f"Received transcript: {transcript}")
                logger.info(f"Current ordering token: {ordering_token}")
                conv = json.loads(redis_client.get(f'{ordering_token}_conversation'))
                logger.info(f"Current conversation state: {conv}")
                try:
                    transcript_send = {"type": "cus", "transcript": transcript, "time": datetime.now().isoformat()}
                    logger.info(f"Sending transcript to WebSocket: {transcript_send}")
                    await fast_socket.send_json(transcript_send)
                    logger.info(f"Sending transcript: {transcript}")
                    conv.append(transcript_send)
                except Exception as e:
                    logger.error(f"Error sending transcript: {e}")
                    await fast_socket.send_json({"type": "error", "msg": "Failed to send transcript"})
                    return
                try:
                    response, status, order_diff = await call_llm(transcript, ordering_token)
                    llm_send = {"type": "llm", "response": response, "time": datetime.now().isoformat()}
                    logger.info(f"LLM response: {response}")
                    await fast_socket.send_json(llm_send)
                    await fast_socket.send_json({"type": "order", "diff": order_diff})
                    conv.append(llm_send)
                except Exception as e:
                    logger.error(f"Error calling LLM: {e}")
                    await fast_socket.send_json({"type": "error", "msg": "Failed to call LLM"})
                    return
                redis_client.set(f'{ordering_token}_conversation', json.dumps(conv))
                if status:
                    end_send = {"type": "end", "msg": "Conversation ended"}
                    await fast_socket.send_json(end_send)
                    conv.append(end_send)
                    redis_client.set(f'{ordering_token}_conversation', json.dumps(conv))
                    await fast_socket.close()

    deepgram_socket = await connect_to_deepgram(get_transcript)
    return deepgram_socket

async def connect_to_deepgram(transcript_received_handler: Callable[[Dict], None]):
    try:
        # Use async websocket client
        dg_connection = dg_client.listen.asyncwebsocket.v("1")
        
        # Fix the on_message function signature and make it async
        # Fix the on_message function signature and make it async
        async def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            
            if sentence:
                await transcript_received_handler({"channel": {"alternatives": [{"transcript": sentence}]}})
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        
        options = LiveOptions(
            model='nova-2',  # Use nova-2 or nova-3 as in official example
            language='zh-TW',
            punctuate=True,
            interim_results=False
        )
        
        # Use async start
        if await dg_connection.start(options) is False:
            raise Exception("Failed to start connection")
            
        return dg_connection
    except Exception as e:
        raise Exception(f'Could not open socket: {e}')
    
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

    response, neww_order_state = order_real_time(
        text, 
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