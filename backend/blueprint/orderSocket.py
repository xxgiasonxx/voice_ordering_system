"""
Legacy orderSocket - DEPRECATED: ASR functionality has been moved to asr_stream.py
This file is kept for backward compatibility but the /asr WebSocket endpoint
is now served by asr_stream.py (audioSSE router).
"""
from fastapi import APIRouter, WebSocket, Cookie
from fastapi.responses import JSONResponse
from rag.rag_morning_eat import order_real_time
from setup import cus_choice, vectorstore, conn, redis_client
import os
import logging
import json
from dotenv import load_dotenv
from typing import Dict
from blueprint.token import decrypt_token, verify_token
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

audioWS = APIRouter()


@audioWS.get('/history/legacy')
async def get_conversation_history_legacy(ordering_token: str = Cookie(None)):
    logger.warning("Legacy /history/legacy endpoint called. Use /history from asr_stream instead.")
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


def order_diff_state(order_state: Dict, new_order_state: Dict):
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
                modified_items.append({
                    'old': old_item,
                    'new': new_item
                })

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
