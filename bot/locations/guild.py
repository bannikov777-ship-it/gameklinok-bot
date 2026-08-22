# locations/guild.py - в начале файла
import sqlite3
import asyncio
from core import get_character_async, update_user_async, send_message, get_character_by_id_async, DB_NAME, get_user_async
from guild import (
    get_guild_by_character, get_guild_members, get_guild_storage, 
    guild_exp_to_next_level, get_all_guilds, set_rank, kick_member,
    add_to_guild_storage, remove_from_guild_storage, send_guild_message
)
from keyboards import (
    get_guild_keyboard, get_guild_manage_keyboard, get_guild_chat_keyboard, 
    get_back_keyboard, get_guild_menu_keyboard, get_member_action_keyboard,
    get_guild_storage_keyboard
)
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from .base import navigate_to

GUILD_IMAGE = 'photo-240828623_456239327'
GUILD_MEMBERS_IMAGE = 'photo-240828623_456239327'
GUILD_STORAGE_IMAGE = 'photo-240828623_456239328'

# ... остальной код без изменений

async def show_guild(vk, user_id):
    """Показ гильдии"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        keyboard = get_guild_menu_keyboard()
        await send_message(vk, user_id, '🏰 Вы не состоите в гильдии. Что желаете сделать?', keyboard, attachment=GUILD_IMAGE)
        return
    leader = await get_character_by_id_async(guild['leader_id'])
    leader_name = leader['name'] if leader else 'Неизвестно'
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT rank FROM guild_members WHERE guild_id = ? AND character_id = ?', (guild['id'], char['id']))
    row = cur.fetchone()
    conn.close()
    my_rank = row[0] if row else 'Участник'
    exp_current = guild['exp']
    exp_needed = guild_exp_to_next_level(guild['level'])
    progress = min(1.0, exp_current / exp_needed) if exp_needed > 0 else 0
    bar_length = 10
    filled = int(progress * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    text = f"🏰 {guild['name']}\nУровень: {guild['level']} | Опыт: {exp_current} / {exp_needed} [{bar}]\n💰{guild['silver']}\nЛидер: {leader_name}\nУчастников: {len(get_guild_members(guild['id']))}/{guild['max_members']}"
    keyboard = get_guild_keyboard(guild, my_rank)
    await send_message(vk, user_id, text, keyboard, attachment=GUILD_IMAGE)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'city'
    await update_user_async(user_id, state='guild', context=context)


async def show_guild_donate(vk, user_id):
    """Пополнение казны гильдии"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    await send_message(vk, user_id, 'Введите сумму серебра для пополнения казны:')
    await update_user_async(user_id, state='awaiting_guild_donate', context={'parent_state': 'guild'})


async def show_guild_donate_confirm(vk, user_id, amount):
    """Подтверждение пополнения казны"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    if char['silver'] < amount:
        await send_message(vk, user_id, f'❌ Недостаточно серебра! Нужно {amount}💰.', get_back_keyboard('гильдию'))
        return
    if amount <= 0:
        await send_message(vk, user_id, 'Сумма должна быть положительной.', get_back_keyboard('гильдию'))
        return
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute('UPDATE characters SET silver = silver - ? WHERE id = ?', (amount, char['id']))
        cur.execute('UPDATE guilds SET silver = silver + ? WHERE id = ?', (amount, guild['id']))
        conn.commit()
        await send_message(vk, user_id, f'✅ Вы внесли {amount}💰 в казну гильдии!', get_back_keyboard('гильдию'))
        await show_guild(vk, user_id)
    except Exception as e:
        conn.rollback()
        await send_message(vk, user_id, f'❌ Ошибка при пополнении: {e}', get_back_keyboard('гильдию'))
    finally:
        conn.close()


async def show_guild_withdraw(vk, user_id):
    """Снятие денег из казны (только лидер)"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    if guild['leader_id'] != char['id']:
        await send_message(vk, user_id, '❌ Только лидер может брать деньги из казны.', get_back_keyboard('гильдию'))
        return
    await send_message(vk, user_id, f'💰 Введите сумму для снятия из казны (доступно: {guild["silver"]}💰):')
    await update_user_async(user_id, state='awaiting_guild_withdraw', context={'parent_state': 'guild'})


async def show_guild_withdraw_confirm(vk, user_id, amount):
    """Подтверждение снятия из казны"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    if guild['leader_id'] != char['id']:
        await send_message(vk, user_id, '❌ Только лидер может брать деньги из казны.', get_back_keyboard('гильдию'))
        return
    if guild['silver'] < amount:
        await send_message(vk, user_id, f'❌ В казне недостаточно серебра! Доступно: {guild["silver"]}💰.', get_back_keyboard('гильдию'))
        return
    if amount <= 0:
        await send_message(vk, user_id, '❌ Сумма должна быть положительной.', get_back_keyboard('гильдию'))
        return
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute('UPDATE guilds SET silver = silver - ? WHERE id = ?', (amount, guild['id']))
        cur.execute('UPDATE characters SET silver = silver + ? WHERE id = ?', (amount, char['id']))
        conn.commit()
        await send_message(vk, user_id, f'✅ Вы сняли {amount}💰 из казны гильдии!', get_back_keyboard('гильдию'))
        await show_guild(vk, user_id)
    except Exception as e:
        conn.rollback()
        await send_message(vk, user_id, f'❌ Ошибка при снятии: {e}', get_back_keyboard('гильдию'))
    finally:
        conn.close()


async def show_guild_members(vk, user_id):
    """Список участников гильдии"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    members = get_guild_members(guild['id'])
    lines = [f"👥 Участники гильдии «{guild['name']}»:"]
    for m in members:
        lines.append(f"• {m['name']} ({m['rank']})")
    await send_message(vk, user_id, "\n".join(lines), get_back_keyboard('гильдию'), attachment=GUILD_MEMBERS_IMAGE)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'guild'
    await update_user_async(user_id, state='guild_members', context=context)


async def show_guild_storage(vk, user_id):
    """Склад гильдии"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    items = await asyncio.to_thread(get_guild_storage, guild['id'])
    if not items:
        await send_message(vk, user_id, '📦 Склад гильдии пуст.', get_guild_storage_keyboard([]), attachment=GUILD_STORAGE_IMAGE)
    else:
        keyboard = get_guild_storage_keyboard(items)
        await send_message(vk, user_id, '📦 Склад гильдии:', keyboard, attachment=GUILD_STORAGE_IMAGE)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'guild'
    await update_user_async(user_id, state='guild_storage', context=context)


async def show_guild_stats(vk, user_id):
    """Статистика гильдии"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT c.name, c.level, c.guild_exp_contributed, c.guild_quests_completed
        FROM guild_members gm
        JOIN characters c ON gm.character_id = c.id
        WHERE gm.guild_id = ?
        ORDER BY c.guild_exp_contributed DESC
    ''', (guild['id'],))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await send_message(vk, user_id, 'В гильдии пока нет участников.', get_back_keyboard('гильдию'))
        return
    text = f"📊 Статистика гильдии «{guild['name']}»:\n\n"
    for name, level, guild_exp, quests_done in rows:
        text += f"• {name} | Ур.{level} | Опыт: {guild_exp} | Заданий: {quests_done}\n"
    await send_message(vk, user_id, text, get_back_keyboard('гильдию'))
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'guild'
    await update_user_async(user_id, state='guild_stats', context=context)


async def show_guild_manage(vk, user_id):
    """Управление гильдией"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT rank FROM guild_members WHERE guild_id = ? AND character_id = ?', (guild['id'], char['id']))
    row = cur.fetchone()
    conn.close()
    my_rank = row[0] if row else 'Участник'
    if my_rank not in ('Лидер', 'Заместитель'):
        await send_message(vk, user_id, 'У вас нет прав на управление гильдией.', get_back_keyboard('гильдию'))
        return
    members = get_guild_members(guild['id'])
    keyboard = get_guild_manage_keyboard(members, my_rank)
    await send_message(vk, user_id, '⚙️ Управление гильдией\nВыберите участника:', keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'guild'
    await update_user_async(user_id, state='guild_manage', context=context)


async def show_guild_manage_member(vk, user_id, member_id):
    """Управление конкретным участником"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT rank FROM guild_members WHERE guild_id = ? AND character_id = ?', (guild['id'], char['id']))
    row = cur.fetchone()
    conn.close()
    my_rank = row[0] if row else 'Участник'
    if my_rank not in ('Лидер', 'Заместитель'):
        await send_message(vk, user_id, 'У вас нет прав на управление гильдией.', get_back_keyboard('гильдию'))
        return
    target = None
    members = get_guild_members(guild['id'])
    for m in members:
        if m['id'] == member_id:
            target = m
            break
    if not target:
        await send_message(vk, user_id, 'Участник не найден.', get_back_keyboard('гильдию'))
        return
    if target['rank'] == 'Лидер':
        await send_message(vk, user_id, 'Нельзя управлять лидером.', get_back_keyboard('гильдию'))
        return
    keyboard = get_member_action_keyboard(member_id, target['rank'])
    await send_message(vk, user_id, f"⚙️ Управление участником {target['name']}\nТекущий ранг: {target['rank']}", keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'guild_manage'
    await update_user_async(user_id, state='guild_manage_member', context=context)


async def show_guild_chat(vk, user_id):
    """Чат гильдии"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    keyboard = get_guild_chat_keyboard()
    await send_message(vk, user_id, '💬 Чат гильдии\nНапишите сообщение, и оно будет отправлено всем участникам.', keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'guild'
    await update_user_async(user_id, state='guild_chat', context=context)