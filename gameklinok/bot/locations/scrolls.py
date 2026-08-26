# locations/scrolls.py
import sqlite3
from config import DB_NAME
from core import get_character_async, send_message, update_user_async, recalc_stats_async
from keyboards import get_back_keyboard
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


async def show_scrolls(vk, user_id):
    """Показ доступных свитков"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    # Получаем свитки игрока
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute('''
        SELECT pc.id, pc.quantity, ct.name, ct.icon, ct.description, ct.restore_type
        FROM player_consumables pc
        JOIN consumable_templates ct ON pc.consumable_template_id = ct.id
        WHERE pc.owner_id = ? AND ct.restore_type IN ('curse_remove', 'scroll')
    ''', (char['id'],))
    scrolls = cur.fetchall()
    conn.close()
    
    if not scrolls:
        await send_message(vk, user_id, '📜 У вас нет свитков.\n\nКупить свитки можно в 💎 Премиум магазине.', get_back_keyboard('инвентарь'))
        return
    
    text = "📜 Ваши свитки:\n\n"
    keyboard = VkKeyboard()
    
    # Показываем статус проклятия
    debuff = char.get('debuff', 0)
    if debuff > 0:
        debuff_names = {
            1: '☠️ Проклятие (-30% стат)',
            2: '🔥 Печать башни (-50% стат)'
        }
        text += f"⚠️ Активно: {debuff_names.get(debuff, 'Неизвестное проклятие')}\n\n"
    else:
        text += "✅ Проклятий нет\n\n"
    
    # Нумеруем свитки для кнопок
    scroll_number = 1
    for scroll in scrolls:
        scroll_id, quantity, name, icon, description, restore_type = scroll
        text += f"{icon} {name} (x{quantity})\n📝 {description}\n\n"
        
        keyboard.add_button(f"📜 Использовать #{scroll_number}", color=VkKeyboardColor.PRIMARY,
                           payload={'cmd': 'scroll_use', 'scroll_id': scroll_id, 'type': restore_type})
        keyboard.add_line()
        scroll_number += 1
    
    keyboard.add_button('👤 В профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_profile'})  # ✅ исправлено
    
    await send_message(vk, user_id, text, keyboard)
    await update_user_async(user_id, state='scrolls', context={'parent_state': 'profile'})  # ✅ исправлено


async def use_curse_remove_scroll(vk, user_id, scroll_id):
    """Использование свитка снятия проклятия"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    debuff = char.get('debuff', 0)
    if debuff == 0:
        await send_message(vk, user_id, '❌ У вас нет активного проклятия или печати.\n\nСвиток сохранён.', get_back_keyboard('свитки'))
        await show_scrolls(vk, user_id)
        return
    
    debuff_names = {
        1: '☠️ Проклятие (-30% стат)',
        2: '🔥 Печать башни (-50% стат)'
    }
    debuff_name = debuff_names.get(debuff, 'Неизвестное проклятие')
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute('SELECT quantity FROM player_consumables WHERE id = ? AND owner_id = ?', (scroll_id, char['id']))
    row = cur.fetchone()
    if not row or row[0] <= 0:
        conn.close()
        await send_message(vk, user_id, '❌ У вас нет этого свитка.', get_back_keyboard('свитки'))
        await show_scrolls(vk, user_id)
        return
    
    cur.execute('UPDATE characters SET debuff = 0 WHERE id = ?', (char['id'],))
    
    if row[0] == 1:
        cur.execute('DELETE FROM player_consumables WHERE id = ?', (scroll_id,))
    else:
        cur.execute('UPDATE player_consumables SET quantity = quantity - 1 WHERE id = ?', (scroll_id,))
    
    conn.commit()
    conn.close()
    
    await recalc_stats_async(char['id'])
    
    await send_message(vk, user_id, 
        f'✅ {debuff_name} снято!\n'
        f'Статы восстановлены.',
        get_back_keyboard('профиль'))  # ✅ исправлено
    await show_scrolls(vk, user_id)


async def use_scroll(vk, user_id, scroll_id, scroll_type):
    """Универсальная функция использования свитка"""
    if scroll_type == 'curse_remove':
        await use_curse_remove_scroll(vk, user_id, scroll_id)
    else:
        await send_message(vk, user_id, f'❌ Неизвестный тип свитка: {scroll_type}', get_back_keyboard('профиль'))
        await show_scrolls(vk, user_id)