# locations/inventory.py (исправленный - ID в начале, статы остаются)

import sqlite3
from config import DB_NAME
from core import (
    get_character_async, update_user_async, send_message, get_user_async,
    get_inventory, get_equipment, get_player_consumables, equip_item, unequip_item, recalc_stats_async
)
from keyboards import get_back_keyboard
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def get_rarity_icon(rarity):
    """Получение иконки редкости (только иконка)"""
    rarity_icons = {
        1: '⚪',
        2: '🟢',
        3: '🔵',
        4: '🟣',
        5: '🟠'
    }
    return rarity_icons.get(rarity, '⚪')


def get_rarity_stars(rarity):
    """Получение звёзд редкости"""
    return '⭐' * rarity


def get_item_detail_text(item):
    """Формирование детального описания предмета (только статы)"""
    parts = []
    
    if item.get('attack', 0) > 0:
        parts.append(f"+{item['attack']} атк")
    if item.get('defense', 0) > 0:
        parts.append(f"+{item['defense']} защ")
    if item.get('hp', 0) > 0:
        parts.append(f"+{item['hp']} HP")
    if item.get('mana', 0) > 0:
        parts.append(f"+{item['mana']} маны")
    if item.get('bonus_crit', 0) != 0:
        crit = item['bonus_crit']
        parts.append(f"💥{crit:+}% крит")
    if item.get('bonus_dodge', 0) != 0:
        dodge = item['bonus_dodge']
        parts.append(f"💨{dodge:+}% уворот")
    
    return ", ".join(parts) if parts else ""


async def show_inventory(vk, user_id):
    """Показ инвентаря с детальным отображением и ID"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    # Получаем данные
    inv_items = get_inventory(char['id'])
    equipment = get_equipment(char['id'])
    consumables = get_player_consumables(char['id'])
    
    # Формируем текст
    text = "🎒 Инвентарь\n\n"
    
    # Экипировка с ID в начале
    text += "🛡️ Экипировка (введите ID для снятия):\n"
    slots = {
        'head': ('🎩', 'Голова'),
        'weapon_right': ('🗡️', 'Правая рука'),
        'weapon_left': ('🛡️', 'Левая рука'),
        'armor': ('🛡️', 'Торс'),
        'boots': ('👢', 'Сапоги')
    }
    
    # Проверяем, открыта ли левая рука
    show_left = char.get('class') and char.get('level', 0) >= 20
    
    for slot_key, (icon, slot_name) in slots.items():
        if slot_key == 'weapon_left' and not show_left:
            continue
        if slot_key in equipment and equipment[slot_key]:
            item = equipment[slot_key]
            detail = get_item_detail_text(item)
            rarity_icon = get_rarity_icon(item.get('rarity', 1))
            stars = get_rarity_stars(item.get('rarity', 1))
            upgrade = f" [+{item.get('upgrade_level', 0)}]" if item.get('upgrade_level', 0) > 0 else ""
            
            # ✅ ID в начале, статы в конце
            if detail:
                text += f"  {icon} {slot_name}: 📌ID:{item['id']} {item['icon']} {item['name']} (Ур.{item.get('level', 1)}){upgrade} {rarity_icon}{stars} ({detail})\n"
            else:
                text += f"  {icon} {slot_name}: 📌ID:{item['id']} {item['icon']} {item['name']} (Ур.{item.get('level', 1)}){upgrade} {rarity_icon}{stars}\n"
        else:
            text += f"  {icon} {slot_name}: —\n"
    
    if not show_left:
        text += "\n🛡️ Левая рука откроется после выбора класса (20 уровень)\n"
    
    # Предметы в сумке с ID в начале
    text += "\n🎒 Предметы в сумке (введите ID для экипировки):\n"
    if inv_items:
        for item in inv_items:
            detail = get_item_detail_text(item)
            rarity_icon = get_rarity_icon(item.get('rarity', 1))
            stars = get_rarity_stars(item.get('rarity', 1))
            upgrade = f" [+{item.get('upgrade_level', 0)}]" if item.get('upgrade_level', 0) > 0 else ""
            qty_text = f" (x{item['quantity']})" if item.get('quantity', 1) > 1 else ""
            
            # ✅ ID в начале, статы в конце
            if detail:
                text += f"  📌ID:{item['id']} {item['icon']} {item['name']} (Ур.{item.get('level', 1)}){upgrade} {rarity_icon}{stars} ({detail}){qty_text}\n"
            else:
                text += f"  📌ID:{item['id']} {item['icon']} {item['name']} (Ур.{item.get('level', 1)}){upgrade} {rarity_icon}{stars}{qty_text}\n"
    else:
        text += "  Нет предметов\n"
    
    # Расходники
    text += "\n🧪 Расходники:\n"
    if consumables:
        # Отделяем свитки от остальных расходников
        scrolls = []
        other_consumables = []
        for c in consumables:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute('SELECT restore_type FROM consumable_templates WHERE id = ?', (c['id'],))
            row = cur.fetchone()
            conn.close()
            if row and row[0] in ('curse_remove', 'scroll'):
                scrolls.append(c)
            else:
                other_consumables.append(c)
        
        # Показываем обычные расходники
        for c in other_consumables:
            text += f"  {c['icon']} {c['name']} (x{c['quantity']})\n"
        
        # Показываем свитки отдельно
        if scrolls:
            text += "\n  📜 Свитки:\n"
            for c in scrolls:
                text += f"    {c['icon']} {c['name']} (x{c['quantity']})\n"
    else:
        text += "  Нет расходников\n"
    
    # Ресурсы/Травы (если есть)
    try:
        from core import get_player_resources
        resources = get_player_resources(char['id'])
        if resources:
            text += "\n🎁 Ресурсы:\n"
            for r in resources:
                text += f"  {r['icon']} {r['name']} (x{r['quantity']})\n"
    except:
        pass
    
    # Клавиатура
    keyboard = VkKeyboard()
    keyboard.add_button('📥 Экипировать по ID', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'inventory_equip_prompt'})
    keyboard.add_button('📤 Снять по ID', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'inventory_unequip_prompt'})
    keyboard.add_line()
    keyboard.add_button('📜 Свитки', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'scrolls'})
    keyboard.add_line()
    keyboard.add_button('👤 В профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_profile'})
    
    await send_message(vk, user_id, text, keyboard)
    await update_user_async(user_id, state='inventory', context={'parent_state': 'profile'})


async def show_inventory_equip_prompt(vk, user_id):
    """Запрос ID предмета для экипировки"""
    await send_message(vk, user_id, '📝 Введите ID предмета, который хотите экипировать (можно посмотреть в инвентаре):')
    await update_user_async(user_id, state='awaiting_inventory_equip_id', context={'parent_state': 'inventory'})


async def show_inventory_equip_by_id(vk, user_id, item_id):
    """Экипировка предмета по ID"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    # Проверяем, существует ли предмет и принадлежит ли игроку
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT pi.id, pi.template_id, pi.level, pi.rarity, pi.upgrade_level, it.slot
        FROM player_items pi
        JOIN item_templates it ON pi.template_id = it.id
        WHERE pi.id = ? AND pi.owner_id = ? AND pi.quantity > 0
    ''', (item_id, char['id']))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        await send_message(vk, user_id, '❌ Предмет не найден или не принадлежит вам.', get_back_keyboard('инвентарь'))
        return
    
    slot = row[5]
    
    # Экипируем предмет
    success = equip_item(char['id'], item_id, slot)
    if success:
        await recalc_stats_async(char['id'])
        await send_message(vk, user_id, f'✅ Предмет экипирован в слот {slot}!', get_back_keyboard('инвентарь'))
    else:
        await send_message(vk, user_id, '❌ Не удалось экипировать предмет.', get_back_keyboard('инвентарь'))
    
    await show_inventory(vk, user_id)


async def show_inventory_equip(vk, user_id):
    """Показ предметов для экипировки (старый метод, оставлен для совместимости)"""
    await show_inventory_equip_prompt(vk, user_id)


async def show_inventory_unequip_prompt(vk, user_id):
    """Запрос ID предмета для снятия (без лишних шагов)"""
    await send_message(vk, user_id, '📝 Введите ID предмета, который хотите снять (можно посмотреть в экипировке):')
    await update_user_async(user_id, state='awaiting_inventory_unequip_id', context={'parent_state': 'inventory'})


async def show_inventory_unequip_by_id(vk, user_id, item_id):
    """Снятие предмета по ID (без лишних шагов)"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    # Проверяем, принадлежит ли предмет игроку и надет ли он
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT slot
        FROM equipment
        WHERE character_id = ? AND player_item_id = ?
    ''', (char['id'], item_id))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        await send_message(vk, user_id, '❌ Предмет не надет или не принадлежит вам.', get_back_keyboard('инвентарь'))
        await show_inventory(vk, user_id)
        return
    
    slot = row[0]
    
    # Снимаем предмет
    success = unequip_item(char['id'], slot)
    if success:
        await recalc_stats_async(char['id'])
        await send_message(vk, user_id, f'✅ Предмет снят с слота {slot}!', get_back_keyboard('инвентарь'))
    else:
        await send_message(vk, user_id, '❌ Не удалось снять предмет.', get_back_keyboard('инвентарь'))
    
    await show_inventory(vk, user_id)


async def show_inventory_unequip(vk, user_id):
    """Устаревший метод - теперь просто вызываем промпт"""
    await show_inventory_unequip_prompt(vk, user_id)


async def show_inventory_equip_select(vk, user_id, slot):
    """Показ предметов для конкретного слота (устаревший метод)"""
    await show_inventory_equip_prompt(vk, user_id)