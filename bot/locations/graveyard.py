# locations/graveyard.py
import random
import asyncio
from core import get_character_async, update_user_async, send_message, get_user_async
from battle import start_battle, delay_with_message
from keyboards import get_back_keyboard
from .base import GRAVEYARD_IMAGE, GRAVEYARD_DEEP_IMAGE, GRAVEYARD_WANDER_IMAGE

async def show_graveyard(vk, user_id):
    """Показ кладбища"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    if char['level'] < 10:
        await send_message(vk, user_id, f'🪦 Кладбище доступно с 10 уровня. Ваш уровень: {char["level"]}.', get_back_keyboard('город'))
        return
    
    # Показываем картинку входа на кладбище
    await send_message(vk, user_id, "🪦 Вы входите на кладбище...", attachment=GRAVEYARD_IMAGE)
    
    # Задержка 2-5 секунд
    await asyncio.sleep(random.randint(2, 5))
    
    user_data = await get_user_async(user_id)
    context = user_data['context']
    if 'graveyard_depth' not in context:
        context['graveyard_depth'] = 0
        await update_user_async(user_id, context=context)
    depth = context.get('graveyard_depth', 0)
    await start_battle(vk, user_id, 'graveyard', depth)

async def graveyard_deep(vk, user_id):
    """Углубление на кладбище"""
    # Показываем картинку углубления
    await send_message(vk, user_id, "🪦 Вы углубляетесь на кладбище...", attachment=GRAVEYARD_DEEP_IMAGE)
    
    # Задержка 3-8 секунд
    await asyncio.sleep(random.randint(3, 8))
    
    user_data = await get_user_async(user_id)
    context = user_data['context']
    depth = context.get('graveyard_depth', 0) + 1
    context['graveyard_depth'] = depth
    await update_user_async(user_id, context=context)
    await start_battle(vk, user_id, 'graveyard', depth)

async def graveyard_wander(vk, user_id):
    """Бродяжничество на кладбище"""
    # Показываем картинку поиска
    await send_message(vk, user_id, "🔍 Вы ищете следы на кладбище...", attachment=GRAVEYARD_WANDER_IMAGE)
    
    # Задержка 3-8 секунд
    await asyncio.sleep(random.randint(3, 8))
    
    user_data = await get_user_async(user_id)
    depth = user_data['context'].get('graveyard_depth', 0)
    await start_battle(vk, user_id, 'graveyard', depth)

async def back_to_exit(vk, user_id):
    """Возврат к выходу с кладбища"""
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context.pop('graveyard_depth', None)
    await update_user_async(user_id, context=context)
    await delay_with_message(vk, user_id, "🚶 Вы выходите с кладбища...", attachment=GRAVEYARD_IMAGE, delay_range=(2, 4))
    from .exit import show_exit
    await show_exit(vk, user_id)