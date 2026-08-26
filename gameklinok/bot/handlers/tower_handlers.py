# handlers/tower_handlers.py
import asyncio
from core import get_character_async, send_message, update_user_async, get_user_async
from tower import get_tower_party, create_tower_party, join_tower_party, start_tower_battle, leave_tower, rest_in_tower, handle_tower_accept_guild_invite
from keyboards import get_back_keyboard
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from locations import show_tower, show_meadow, show_church

TOWER_IMAGE = 'photo-240828623_456239325'

async def handle_tower_commands(vk, user_id, cmd, payload=None):
    """Обработчик команд башни"""
    if cmd == 'tower':
        await show_tower(vk, user_id)
        return True
    elif cmd == 'tower_create_party':
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('луг'))
            return True
        success, msg = await create_tower_party(vk, char['id'])
        await send_message(vk, user_id, msg)
        await show_tower(vk, user_id)
        return True
    elif cmd == 'tower_leave':
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('луг'))
            return True
        success, msg = await leave_tower(char['id'])
        await send_message(vk, user_id, msg)
        await show_meadow(vk, user_id)
        return True
    elif cmd == 'tower_rest':
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('луг'))
            return True
        success, msg = await rest_in_tower(char['id'])
        await send_message(vk, user_id, msg)
        await show_tower(vk, user_id)
        return True
    elif cmd == 'tower_accept_guild_invite':
        leader_id = payload.get('leader_id') if payload else None
        if leader_id:
            await handle_tower_accept_guild_invite(vk, user_id, leader_id)
        return True
    elif cmd == 'tower_decline_invite':
        await send_message(vk, user_id, '❌ Вы отказались от приглашения.')
        await show_meadow(vk, user_id)
        return True
    elif cmd == 'tower_start_battle':
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.')
            return True
        party = await asyncio.to_thread(get_tower_party, char['id'])
        if not party:
            await send_message(vk, user_id, 'Вы не в группе.')
            return True
        if party['leader_id'] != char['id']:
            await send_message(vk, user_id, 'Только лидер может начать бой.')
            return True
        success, msg, log = await start_tower_battle(vk, char['id'])
        if success:
            await show_tower(vk, user_id)
        else:
            # При поражении лидер уже перенаправлен в Собор в process_tower_battle
            # Но на всякий случай проверяем и не дублируем
            await send_message(vk, user_id, f'❌ {msg}')
            # Проверяем состояние пользователя
            user_data = await get_user_async(user_id)
            # Если пользователь еще не в Соборе, отправляем его туда
            if user_data['state'] != 'church':
                await update_user_async(user_id, state='church', context={'parent_state': 'meadow'})
                await show_church(vk, user_id)
            # Если уже в Соборе - ничего не делаем (уже открыт)
        return True
    return False