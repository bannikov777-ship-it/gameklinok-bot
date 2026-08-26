# locations/hunters.py
import asyncio
from core import get_character_async, update_user_async, send_message, get_user_async
from keyboards import get_hunters_keyboard, get_back_keyboard
from quests import get_available_quests, take_quest, get_active_quests, get_completed_quests_count_today
from resources import sell_all_resources
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

HUNTERS_IMAGE = 'photo-240828623_456239030'
HUNTERS_MY_QUESTS_IMAGE = 'photo-240828623_456239330'

async def show_hunters(vk, user_id):
    """Показ гильдии охотников"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    await send_message(vk, user_id, '🏹 Гильдия охотников – здесь вы можете сдать трофеи и взять задания на убийство монстров.',
                       get_hunters_keyboard(), attachment=HUNTERS_IMAGE)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'city'
    await update_user_async(user_id, state='hunters', context=context)


async def show_hunters_sell(vk, user_id):
    """Продажа трофеев"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    total, msg = await asyncio.to_thread(sell_all_resources, char['id'])
    await send_message(vk, user_id, msg, get_back_keyboard('гильдию охотников'))
    await show_hunters(vk, user_id)


async def show_hunters_quests(vk, user_id):
    """Показ доступных заданий"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    completed_today = get_completed_quests_count_today(char['id'])
    if completed_today >= 3:
        await send_message(vk, user_id, '📅 Вы уже выполнили 3 задания сегодня. Приходите завтра!', get_back_keyboard('гильдию охотников'))
        return
    available = get_available_quests(char['id'])
    if not available:
        await send_message(vk, user_id, '📭 Нет доступных заданий (возможно, все уже взяты).', get_back_keyboard('гильдию охотников'))
        return
    text = "📜 Доступные задания:\n\n"
    keyboard = VkKeyboard()
    for q in available:
        text += f"🔹 {q['name']} – {q['description']} (убить {q['target_count']} монстров)\nНаграда: {q['reward_silver']}💰 + {q['reward_potion_count']} средних зелий HP\n"
        keyboard.add_button(f"Взять: {q['name'][:20]}", color=VkKeyboardColor.PRIMARY, 
                           payload={'cmd': 'hunters_take_quest', 'quest_id': q['id']})
        keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'hunters'})
    await send_message(vk, user_id, text, keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'hunters'
    await update_user_async(user_id, state='hunters_quests', context=context)


async def show_hunters_my_quests(vk, user_id):
    """Показ активных заданий"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    quests = get_active_quests(char['id'])
    if not quests:
        await send_message(vk, user_id, 'У вас нет активных заданий.', get_back_keyboard('гильдию охотников'), 
                          attachment=HUNTERS_MY_QUESTS_IMAGE)
        return
    text = "📋 Ваши задания:\n\n"
    for q in quests:
        progress_bar = "█" * int(q['progress'] / q['target'] * 10) + "░" * (10 - int(q['progress'] / q['target'] * 10))
        text += f"🔹 {q['name']} – {q['description']}\nПрогресс: {q['progress']}/{q['target']} [{progress_bar}]\nНаграда: {q['reward_silver']}💰 + {q['reward_potion_count']} зелий\n\n"
    await send_message(vk, user_id, text, get_back_keyboard('гильдию охотников'), attachment=HUNTERS_MY_QUESTS_IMAGE)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'hunters'
    await update_user_async(user_id, state='hunters_my_quests', context=context)


async def show_hunters_take_quest(vk, user_id, quest_id):
    """Взятие задания"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    success, msg = take_quest(char['id'], quest_id)
    if success:
        await send_message(vk, user_id, f'✅ {msg}', get_back_keyboard('гильдию охотников'))
    else:
        await send_message(vk, user_id, f'❌ {msg}', get_back_keyboard('гильдию охотников'))
    await show_hunters(vk, user_id)