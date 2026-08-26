# locations/tower.py
import asyncio
import time
from core import get_character_async, update_user_async, send_message, get_user_async
from tower import get_tower_party, get_tower_boss, start_tower_battle, leave_tower, rest_in_tower
from keyboards import get_back_keyboard, get_sleep_status_keyboard
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

TOWER_IMAGE = 'photo-240828623_456239325'

async def show_tower(vk, user_id):
    """Показ башни"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('луг'))
        return
    party = await asyncio.to_thread(get_tower_party, char['id'])
    if not party:
        keyboard = VkKeyboard()
        keyboard.add_button('🏰 Создать группу', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'tower_create_party'})
        keyboard.add_button('🌿 На луг', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_meadow'})  # ✅ исправлено
        await send_message(vk, user_id, '🗼 Вы у входа в Башню.\n\nВы не состоите в группе. Создайте её, чтобы начать.', keyboard)
    else:
        from core import get_character_by_id_async
        leader = await get_character_by_id_async(party['leader_id'])
        members_text = "\n".join([f"• {(await get_character_by_id_async(m))['name']}" for m in party['members']])
        is_leader = party['leader_id'] == char['id']
        text = f"🗼 Башня – этаж {party['current_floor']}/10\n\n👑 Лидер: {leader['name']}\n👥 Участники:\n{members_text}\n"
        keyboard = VkKeyboard()
        keyboard.add_button('💬 Чат группы', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'tower_chat_show'})
        if is_leader:
            keyboard.add_button('⚔️ Начать бой', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'tower_start_battle'})
        keyboard.add_line()
        keyboard.add_button('🚪 Покинуть группу', color=VkKeyboardColor.NEGATIVE, payload={'cmd': 'tower_leave'})
        keyboard.add_button('🌿 На луг', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_meadow'})  # ✅ исправлено
        await send_message(vk, user_id, text, keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'meadow'
    await update_user_async(user_id, state='tower', context=context)


async def show_tower_chat(vk, user_id):
    """Показ чата группы башни"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    party = await asyncio.to_thread(get_tower_party, char['id'])
    if not party:
        await send_message(vk, user_id, 'Вы не в группе башни.', get_back_keyboard('башня'))
        await show_tower(vk, user_id)
        return
    
    from keyboards import get_tower_chat_keyboard
    keyboard = get_tower_chat_keyboard()
    
    await send_message(vk, user_id, '💬 Чат группы башни\n\nНапишите сообщение, и оно будет отправлено всем участникам группы.', keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'tower'
    await update_user_async(user_id, state='tower_chat', context=context)


async def show_sleep_status(vk, user_id):
    """Показ статуса сна"""
    user_data = await get_user_async(user_id)
    context = user_data['context']
    sleep_end_time = context.get('sleep_end_time')
    if not sleep_end_time:
        await send_message(vk, user_id, 'Вы сейчас не спите.', get_back_keyboard('таверну'))
        return
    remaining = max(0, sleep_end_time - time.time())
    hours = int(remaining // 3600)
    minutes = int((remaining % 3600) // 60)
    seconds = int(remaining % 60)
    await send_message(vk, user_id, f'⏳ До пробуждения осталось: {hours}ч {minutes}м {seconds}с', get_sleep_status_keyboard())