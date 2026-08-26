# handlers/guild_quests.py
from core import get_character_async, send_message, update_user_async
from guild_quests import get_available_guild_quests, take_guild_quest, cancel_guild_quest, get_active_guild_quest
from keyboards import get_back_keyboard
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import asyncio

async def handle_guild_quests(vk, user_id, cmd, payload=None):
    """Обработчик команд гильдейских квестов"""
    if cmd == 'guild_quests':
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return True
        try:
            available = await asyncio.to_thread(get_available_guild_quests, char['id'])
        except Exception as e:
            await send_message(vk, user_id, f'❌ Ошибка при получении квестов: {e}', get_back_keyboard('гильдию'))
            return True
        if not available:
            await send_message(vk, user_id, '📭 Нет доступных гильдейских квестов.', get_back_keyboard('гильдию'))
            return True
        text = "📜 Доступные гильдейские квесты:\n\n"
        keyboard = VkKeyboard()
        for i, q in enumerate(available):
            text += f"🔹 {q['name']} ({q['duration_minutes']} мин.)\n"
            text += f"   🎖 {q['exp_reward']} опыта | 💰 {q['silver_reward']} серебра\n"
            if q['extra_reward_type']:
                text += f"   🎁 + доп. награда\n"
            text += "\n"
            keyboard.add_button(f"Взять: {q['name'][:20]}", color=VkKeyboardColor.PRIMARY,
                                payload={'cmd': 'guild_quest_take', 'quest_id': q['id']})
            if i % 2 == 1:
                keyboard.add_line()
        keyboard.add_button('🏰 В гильдию', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_guild'})
        await send_message(vk, user_id, text, keyboard)
        return True

    elif cmd == 'guild_quest_take':
        quest_id = payload.get('quest_id')
        if not quest_id:
            await send_message(vk, user_id, 'Ошибка: квест не указан.', get_back_keyboard('гильдию'))
            return True
        success, msg = await take_guild_quest(vk, user_id, quest_id)
        await send_message(vk, user_id, msg)
        from locations import show_guild
        await show_guild(vk, user_id)
        return True

    elif cmd == 'guild_quest_cancel':
        success, msg = await cancel_guild_quest(vk, user_id)
        await send_message(vk, user_id, msg)
        from locations import show_guild
        await show_guild(vk, user_id)
        return True

    elif cmd == 'guild_quest_status':
        quest = await get_active_guild_quest(user_id)
        if not quest:
            await send_message(vk, user_id, 'У вас нет активного квеста.', get_back_keyboard('гильдию'))
            return True
        from datetime import datetime, timezone
        end_time_str = quest['end_time']
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        end_time = end_time.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        remaining = end_time - now
        if remaining.total_seconds() < 0:
            minutes = 0
            seconds = 0
        else:
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
        text = f"📌 Активный квест: {quest['name']}\n"
        text += f"⏱ Осталось: {minutes} мин {seconds} сек\n"
        text += f"🎖 Награда: {quest['exp_reward']} опыта, {quest['silver_reward']} серебра"
        keyboard = VkKeyboard()
        keyboard.add_button('❌ Отменить', color=VkKeyboardColor.NEGATIVE, payload={'cmd': 'guild_quest_cancel'})
        keyboard.add_button('🏰 В гильдию', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_guild'})
        await send_message(vk, user_id, text, keyboard)
        return True

    return False