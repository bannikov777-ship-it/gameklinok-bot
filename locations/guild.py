# locations/guild.py (полностью исправленный - управление по ID, все back заменены на go_*)
import sqlite3
import asyncio
from datetime import datetime
from core import get_character_async, update_user_async, send_message, get_character_by_id_async, DB_NAME, get_user_async
from guild import (
    get_guild_by_character, get_guild_members, get_guild_storage, 
    guild_exp_to_next_level, get_all_guilds, set_rank, kick_member,
    add_to_guild_storage, remove_from_guild_storage, send_guild_message,
    get_guild, get_guild_rank, get_guilds_list, get_guild_applications,
    apply_to_guild, accept_application, reject_application,
    get_guild_applications_count
)
from keyboards import (
    get_guild_keyboard, get_guild_chat_keyboard, 
    get_back_keyboard, get_guild_menu_keyboard,
    get_guild_storage_keyboard
)
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from .base import navigate_to
from core import get_player_items, get_player_crystals

GUILD_IMAGE = 'photo-240828623_456239327'
GUILD_MEMBERS_IMAGE = 'photo-240828623_456239327'
GUILD_STORAGE_IMAGE = 'photo-240828623_456239328'


# ==================== ОСНОВНЫЕ ФУНКЦИИ ГИЛЬДИИ ====================

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
        lines.append(f"• {m['name']} (ID: {m['id']}, {m['rank']})")
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
    
    text = f"📦 Склад гильдии «{guild['name']}»\n"
    text += f"💰 Казна: {guild['silver']} серебра\n\n"
    
    if not items:
        text += "Склад пуст."
    else:
        crystals = [i for i in items if i.get('item_type') == 'crystal']
        equip_items = [i for i in items if i.get('item_type') == 'item']
        
        if crystals:
            text += "💎 Кристаллы:\n"
            for c in crystals:
                text += f"  • (ID: {c['id']}) {c['name']} x{c['quantity']}\n"
            text += "\n"
        
        if equip_items:
            text += "🗡️ Предметы:\n"
            for item in equip_items:
                stats = ""
                if item.get('attack'): stats += f" ⚔️+{item['attack']}"
                if item.get('defense'): stats += f" 🛡️+{item['defense']}"
                if item.get('hp'): stats += f" ❤️+{item['hp']}"
                text += f"  • (ID: {item['id']}) {item['name']} (Ур.{item['level']}){stats} x{item['quantity']}\n"
    
    keyboard = VkKeyboard()
    
    keyboard.add_button('➕ Добавить предмет', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_storage_add'})
    keyboard.add_button('➖ Изъять предмет', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_storage_remove_prompt'})
    keyboard.add_line()
    keyboard.add_button('💰 Внести в казну', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_donate'})
    
    rank = await asyncio.to_thread(get_guild_rank, char['id'], guild['id'])
    if rank == 'Лидер':
        keyboard.add_button('💰 Взять из казны', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_withdraw'})
    
    keyboard.add_line()
    keyboard.add_button('🏰 В гильдию', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_guild'})
    
    await send_message(vk, user_id, text, keyboard, attachment=GUILD_STORAGE_IMAGE)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'guild'
    await update_user_async(user_id, state='guild_storage', context=context)


async def show_guild_storage_add(vk, user_id):
    """Добавление предмета на склад гильдии"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    
    inv_items = get_player_items(char['id'])
    crystals = get_player_crystals(char['id'])
    
    if not inv_items and not crystals:
        await send_message(vk, user_id, 'У вас нет предметов или кристаллов для передачи в склад.', get_back_keyboard('гильдию'))
        return
    
    keyboard = VkKeyboard()
    
    if inv_items:
        keyboard.add_button('🗡️ Предметы', color=VkKeyboardColor.PRIMARY, 
                           payload={'cmd': 'guild_storage_add_items'})
    
    if crystals:
        keyboard.add_button('💎 Кристаллы', color=VkKeyboardColor.PRIMARY, 
                           payload={'cmd': 'guild_storage_add_crystals'})
    
    keyboard.add_line()
    keyboard.add_button('🏰 В гильдию', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_guild'})
    
    await send_message(vk, user_id, 'Что хотите добавить на склад гильдии?', keyboard)


async def show_guild_storage_add_items(vk, user_id):
    """Добавление предметов на склад"""
    char = await get_character_async(user_id)
    if not char:
        return
    
    inv_items = get_player_items(char['id'])
    if not inv_items:
        await send_message(vk, user_id, 'У вас нет предметов для передачи.', get_back_keyboard('гильдию'))
        return
    
    keyboard = VkKeyboard()
    for item in inv_items:
        label = f"{item['icon']} {item['name']} x{item['quantity']}"
        keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                           payload={'cmd': 'guild_storage_add_item_confirm', 'item_id': item['id'], 'type': 'item'})
        keyboard.add_line()
    
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'guild_storage_add'})
    await send_message(vk, user_id, 'Выберите предмет для передачи на склад:', keyboard)


async def show_guild_storage_add_crystals(vk, user_id):
    """Добавление кристаллов на склад"""
    char = await get_character_async(user_id)
    if not char:
        return
    
    crystals = get_player_crystals(char['id'])
    if not crystals:
        await send_message(vk, user_id, 'У вас нет кристаллов для передачи.', get_back_keyboard('гильдию'))
        return
    
    keyboard = VkKeyboard()
    for c in crystals:
        label = f"{c['icon']} {c['name']} x{c['quantity']}"
        keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                           payload={'cmd': 'guild_storage_add_item_confirm', 'item_id': c['id'], 'type': 'crystal'})
        keyboard.add_line()
    
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'guild_storage_add'})
    await send_message(vk, user_id, 'Выберите кристалл для передачи на склад:', keyboard)


async def show_guild_storage_add_item_confirm(vk, user_id, item_id, item_type):
    """Подтверждение добавления предмета на склад"""
    char = await get_character_async(user_id)
    if not char:
        return
    
    success, msg = await asyncio.to_thread(add_to_guild_storage, char['id'], item_id, item_type)
    if success:
        await send_message(vk, user_id, f'✅ {msg}', get_back_keyboard('гильдию'))
    else:
        await send_message(vk, user_id, f'❌ {msg}', get_back_keyboard('гильдию'))
    
    await show_guild_storage(vk, user_id)


async def show_guild_storage_remove_prompt(vk, user_id):
    """Запрос ID предмета для изъятия"""
    char = await get_character_async(user_id)
    if not char:
        return
    
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    
    rank = await asyncio.to_thread(get_guild_rank, char['id'], guild['id'])
    if rank not in ('Лидер', 'Заместитель', 'Офицер'):
        await send_message(vk, user_id, '❌ У вас нет прав на изъятие предметов.', get_back_keyboard('гильдию'))
        return
    
    await update_user_async(user_id, state='awaiting_guild_storage_remove', context={'parent_state': 'guild_storage'})
    
    await send_message(vk, user_id, 
        '📝 Введите ID предмета для изъятия со склада.\n'
        'ID можно посмотреть в списке склада.\n'
        'Количество: 1 (можно изменить в следующем шаге)')


async def show_guild_storage_remove_confirm(vk, user_id, storage_id, quantity=1):
    """Изъятие предмета со склада"""
    char = await get_character_async(user_id)
    if not char:
        return
    
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    
    success, msg = await asyncio.to_thread(remove_from_guild_storage, guild['id'], storage_id, quantity, char['id'])
    if success:
        await send_message(vk, user_id, f'✅ {msg}', get_back_keyboard('гильдию'))
    else:
        await send_message(vk, user_id, f'❌ {msg}', get_back_keyboard('гильдию'))
    
    await show_guild_storage(vk, user_id)


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


# ==================== УПРАВЛЕНИЕ ГИЛЬДИЕЙ ПО ID ====================

async def show_guild_manage(vk, user_id):
    """Управление гильдией - с списком участников"""
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
    
    # Получаем список участников
    members = get_guild_members(guild['id'])
    
    # Формируем текст со списком участников
    text = "⚙️ Управление гильдией\n\n"
    text += "👥 Список участников (ID для управления):\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for m in members:
        if m['id'] == char['id']:
            text += f"👉 {m['name']} (ID: {m['id']}) — {m['rank']} ★ ВЫ\n"
        else:
            text += f"• {m['name']} (ID: {m['id']}) — {m['rank']}\n"
    
    text += "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "📝 Введите ID участника для управления."
    
    keyboard = VkKeyboard()
    keyboard.add_button('📝 Управлять по ID', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_manage_by_id'})
    keyboard.add_line()
    keyboard.add_button('🔄 Обновить список', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'guild_manage'})  # ✅ добавлено
    keyboard.add_button('🏰 В гильдию', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_guild'})
    
    await send_message(vk, user_id, text, keyboard)
    await update_user_async(user_id, state='guild_manage', context={'parent_state': 'guild'})


async def show_guild_manage_by_id(vk, user_id):
    """Запрос ID участника для управления"""
    await send_message(vk, user_id, '📝 Введите ID участника для управления:')
    await update_user_async(user_id, state='awaiting_guild_manage_id', context={'parent_state': 'guild_manage'})


async def show_guild_manage_member_by_id(vk, user_id, member_id):
    """Управление участником по ID"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    
    # Проверяем права
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT rank FROM guild_members WHERE guild_id = ? AND character_id = ?', (guild['id'], char['id']))
    row = cur.fetchone()
    conn.close()
    my_rank = row[0] if row else 'Участник'
    
    if my_rank not in ('Лидер', 'Заместитель'):
        await send_message(vk, user_id, 'У вас нет прав на управление гильдией.', get_back_keyboard('гильдию'))
        return
    
    # Получаем данные участника
    target = None
    members = get_guild_members(guild['id'])
    for m in members:
        if m['id'] == member_id:
            target = m
            break
    
    if not target:
        await send_message(vk, user_id, f'❌ Участник с ID {member_id} не найден в гильдии.', get_back_keyboard('гильдию'))
        return
    
    if target['rank'] == 'Лидер':
        await send_message(vk, user_id, '❌ Нельзя управлять лидером.', get_back_keyboard('гильдию'))
        return
    
    if target['id'] == char['id']:
        await send_message(vk, user_id, '❌ Нельзя управлять самим собой.', get_back_keyboard('гильдию'))
        return
    
    keyboard = VkKeyboard()
    keyboard.add_button('🟢 Назначить офицером', color=VkKeyboardColor.PRIMARY, 
                       payload={'cmd': 'guild_set_rank', 'member_id': member_id, 'rank': 'Офицер'})
    keyboard.add_button('🔵 Назначить заместителем', color=VkKeyboardColor.PRIMARY, 
                       payload={'cmd': 'guild_set_rank', 'member_id': member_id, 'rank': 'Заместитель'})
    keyboard.add_line()
    keyboard.add_button('❌ Исключить', color=VkKeyboardColor.NEGATIVE, 
                       payload={'cmd': 'guild_kick', 'member_id': member_id})
    keyboard.add_line()
    keyboard.add_button('⚙️ В управление', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'guild_manage'})
    
    await send_message(vk, user_id, 
        f"⚙️ Управление участником\n\n"
        f"👤 Игрок: {target['name']}\n"
        f"📊 Текущий ранг: {target['rank']}\n"
        f"📌 ID: {target['id']}\n\n"
        f"Выберите действие:", keyboard)


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


# ==================== СИСТЕМА ЗАЯВОК И ПАГИНАЦИИ ====================

async def show_guild_list(vk, user_id, page=1):
    """Показ списка гильдий с пагинацией"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    guilds, total_pages = await asyncio.to_thread(get_guilds_list, page, 5)
    
    if not guilds:
        await send_message(vk, user_id, '📭 Пока нет гильдий. Создайте свою!', get_back_keyboard('гильдию'))
        return
    
    text = f"📋 Список гильдий (стр. {page}/{total_pages}):\n\n"
    
    icons = ['', '⭐', '🔥', '🌙', '⚔️', '🛡️', '👑', '💎', '🌟', '⚡', '🏰']
    
    for i, g in enumerate(guilds, start=1 + (page - 1) * 5):
        icon = icons[g['level']] if g['level'] < len(icons) else '🏰'
        text += f"{i}. {icon} {g['name']} (Ур.{g['level']}) | Участников: {g['members']}/{g['max_members']} | 💰 {g['silver']}\n"
    
    keyboard = VkKeyboard()
    
    if page > 1:
        keyboard.add_button('⬅️ Назад', color=VkKeyboardColor.PRIMARY, 
                           payload={'cmd': 'guild_list_page', 'page': page - 1})
    if page < total_pages:
        keyboard.add_button('➡️ Вперед', color=VkKeyboardColor.PRIMARY, 
                           payload={'cmd': 'guild_list_page', 'page': page + 1})
    
    if page > 1 or page < total_pages:
        keyboard.add_line()
    
    keyboard.add_button('🔄 Обновить', color=VkKeyboardColor.SECONDARY, 
                       payload={'cmd': 'guild_list_refresh'})
    keyboard.add_button('📝 Подать заявку', color=VkKeyboardColor.PRIMARY, 
                       payload={'cmd': 'guild_apply_prompt'})
    
    keyboard.add_line()
    
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        keyboard.add_button('🛠 Создать гильдию', color=VkKeyboardColor.PRIMARY, 
                           payload={'cmd': 'guild_create'})
        keyboard.add_line()
    
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, 
                       payload={'cmd': 'go_city'})
    
    await send_message(vk, user_id, text, keyboard)


async def show_guild_apply_prompt(vk, user_id):
    await send_message(vk, user_id, 
        '📝 Введите ID гильдии, в которую хотите подать заявку:\n(можно посмотреть в списке гильдий)')
    await update_user_async(user_id, state='awaiting_guild_apply', context={'parent_state': 'guild'})


async def show_guild_apply_confirm(vk, user_id, guild_id):
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    guild = await asyncio.to_thread(get_guild, guild_id)
    if not guild:
        await send_message(vk, user_id, '❌ Гильдия не найдена.', get_back_keyboard('гильдию'))
        return
    
    existing = await asyncio.to_thread(get_guild_by_character, char['id'])
    if existing:
        await send_message(vk, user_id, f'❌ Вы уже состоите в гильдии «{existing["name"]}».', get_back_keyboard('гильдию'))
        return
    
    success, msg = await asyncio.to_thread(apply_to_guild, char['id'], guild_id)
    if success:
        await send_message(vk, user_id, f'✅ {msg}', get_back_keyboard('гильдию'))
        await notify_guild_leadership(vk, guild_id, char)
    else:
        await send_message(vk, user_id, f'❌ {msg}', get_back_keyboard('гильдию'))
    
    await show_guild_list(vk, user_id)


async def notify_guild_leadership(vk, guild_id, applicant):
    members = get_guild_members(guild_id)
    for m in members:
        if m['rank'] in ('Лидер', 'Заместитель', 'Офицер'):
            char = await get_character_by_id_async(m['id'])
            if char:
                await send_message(vk, char['vk_id'],
                    f"📨 Новая заявка в гильдию!\n"
                    f"🧑 Игрок: {applicant['name']} (Ур.{applicant['level']}, {applicant['class'] or 'без класса'})\n"
                    f"📅 Подана: только что\n\n"
                    f"📋 /guild_applications — просмотреть все заявки"
                )


async def show_guild_applications(vk, user_id):
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    
    rank = await asyncio.to_thread(get_guild_rank, char['id'], guild['id'])
    if rank not in ('Лидер', 'Заместитель', 'Офицер'):
        await send_message(vk, user_id, '❌ У вас нет прав на просмотр заявок.', get_back_keyboard('гильдию'))
        return
    
    apps = await asyncio.to_thread(get_guild_applications, guild['id'])
    
    if not apps:
        await send_message(vk, user_id, '📭 Нет новых заявок.', get_back_keyboard('гильдию'))
        return
    
    text = f"📋 Новые заявки в гильдию «{guild['name']}»:\n\n"
    keyboard = VkKeyboard()
    
    for i, app in enumerate(apps, 1):
        created = datetime.fromisoformat(app['created_at'])
        minutes = (datetime.now() - created).seconds // 60
        if minutes < 60:
            time_str = f"{minutes} мин назад"
        else:
            time_str = f"{minutes//60} час назад"
        
        text += f"{i}. 🧑 {app['name']} (Ур.{app['level']}, {app['class']}) | Подана: {time_str}\n"
        
        keyboard.add_button(f"✅ Принять {i}", color=VkKeyboardColor.POSITIVE, 
                           payload={'cmd': 'guild_accept_app', 'app_id': app['id']})
        keyboard.add_button(f"❌ Отклонить {i}", color=VkKeyboardColor.NEGATIVE, 
                           payload={'cmd': 'guild_reject_app', 'app_id': app['id']})
        keyboard.add_line()
    
    keyboard.add_button('🏰 В гильдию', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_guild'})
    
    await send_message(vk, user_id, text, keyboard)


async def show_guild_accept_app(vk, user_id, app_id):
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    
    success, msg = await asyncio.to_thread(accept_application, app_id, char['id'])
    
    if success:
        await send_message(vk, user_id, f'✅ {msg}', get_back_keyboard('гильдию'))
        
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('SELECT player_id FROM guild_applications WHERE id = ?', (app_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            player_id = row[0]
            player_char = await get_character_by_id_async(player_id)
            if player_char:
                await send_message(vk, player_char['vk_id'], 
                    f"✅ Поздравляем! Ваша заявка в гильдию «{guild['name']}» принята!\n"
                    f"Добро пожаловать в семью! 🎉")
    else:
        await send_message(vk, user_id, f'❌ {msg}', get_back_keyboard('гильдию'))
    
    await show_guild_applications(vk, user_id)


async def show_guild_reject_app(vk, user_id, app_id):
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
    if not guild:
        await send_message(vk, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
        return
    
    success, msg = await asyncio.to_thread(reject_application, app_id, char['id'])
    
    if success:
        await send_message(vk, user_id, f'✅ {msg}', get_back_keyboard('гильдию'))
        
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('SELECT player_id FROM guild_applications WHERE id = ?', (app_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            player_id = row[0]
            player_char = await get_character_by_id_async(player_id)
            if player_char:
                await send_message(vk, player_char['vk_id'], 
                    f"❌ Ваша заявка в гильдию отклонена.\n"
                    f"Причина: не указана.")
    else:
        await send_message(vk, user_id, f'❌ {msg}', get_back_keyboard('гильдию'))
    
    await show_guild_applications(vk, user_id)