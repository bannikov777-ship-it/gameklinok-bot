# core/messaging.py
import random
import time
import asyncio

_last_send_time = 0
SEND_DELAY = 0.5

async def send_message(vk, user_id, text, keyboard=None, attachment=None):
    """Асинхронная отправка сообщения"""
    global _last_send_time
    now = time.time()
    diff = now - _last_send_time
    if diff < SEND_DELAY:
        await asyncio.sleep(SEND_DELAY - diff)
    _last_send_time = time.time()

    params = {
        'peer_id': user_id,
        'message': text,
        'random_id': random.randint(1, 2**31),
        'keyboard': keyboard.get_keyboard() if keyboard else None
    }
    if attachment:
        params['attachment'] = attachment
    try:
        await vk.messages.send(**params)
    except Exception as e:
        print(f"⚠️ Ошибка отправки сообщения: {e}")