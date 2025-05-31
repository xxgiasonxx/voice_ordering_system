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
                response = call_llm(transcript, ordering_token)
                await fast_socket.send_text(response)

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
            model='whisper',  # Use nova-2 or nova-3 as in official example
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

# 假設的 LLM 呼叫函數（可替換為 Gemini、OpenAI 或本地模型）
async def call_llm(text: str, token: str) -> str:
    order_state = json.loads(redis_client.get(f'{token}_order_state'))
    new_order_state = {
        "items": order_state.get('items', []),
        "total_price": order_state.get('total_price', 0),
        "status": order_state.get('status', 'start'),
    }
    response, new_order_state = order_real_time(
        text, 
        vectorstore=vectorstore, 
        cus_choice=cus_choice, 
        order_state=new_order_state, 
        conn=conn
    )
    order_state.update(new_order_state)
    redis_client.set(f'{token}_order_state', json.dumps(order_state))
    return response

@audioWS.websocket("/asr")
async def websocket_endpoint(websocket: WebSocket, ordering_token: str = Cookie(None)):
    await websocket.accept()

    try:
        token = decrypt_token(ordering_token)
        token_id = await verify_token(token)
        if not token_id:
            await websocket.send_text("Invalid or expired token")
            await websocket.close(code=1008)
            raise Exception("Invalid or expired token")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        await websocket.send_text("Token verification failed")
        await websocket.close(code=1008)
        return
    try:
        deepgram_socket = await process_audio(websocket, ordering_token=ordering_token) 

        while True:
            data = await websocket.receive_bytes()
            await deepgram_socket.send(data)  # Use await for async send
            call_llm()
    except Exception as e:
        raise Exception(f'Could not process audio: {e}')
    finally:
        # Add finish() call before closing
        if 'deepgram_socket' in locals():
            await deepgram_socket.finish()
        # Only close websocket if it's still open
        if websocket.client_state.name == "CONNECTED":
            await websocket.close()