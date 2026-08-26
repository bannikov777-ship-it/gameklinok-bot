# admin.py (полный исправленный)
import sqlite3
from codes import create_code, get_codes_list, get_codes_stats
from core import send_message, get_character_async
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from config import DB_NAME

# Список администраторов (ID VK)
ADMIN_IDS = [31979968]  # Добавьте свои ID


async def is_admin(user_id):
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


async def admin_create_code(vk, user_id, amount=100, days=30, max_uses=1, description="", reward_type="crystals"):
    """
    Создание промокода администратором
    
    Args:
        vk: объект VK API
        user_id: ID администратора
        amount: количество кристаллов или серебра
        days: срок действия в днях
        max_uses: максимальное количество использований
        description: описание кода
        reward_type: тип награды ("crystals" или "silver")
    """
    if not await is_admin(user_id):
        await send_message(vk, user_id, '❌ Доступ запрещён. Только для администраторов.')
        return
    
    code = create_code(
        amount=amount,
        expires_days=days,
        max_uses=max_uses,
        description=description or f"{amount} {'💎 кристаллов' if reward_type == 'crystals' else '💰 серебра'}"
    )
    
    # Сохраняем тип награды в отдельную таблицу или в description
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Добавляем колонку reward_type если её нет
    cur.execute("PRAGMA table_info(promo_codes)")
    columns = [col[1] for col in cur.fetchall()]
    if 'reward_type' not in columns:
        cur.execute('ALTER TABLE promo_codes ADD COLUMN reward_type TEXT DEFAULT "crystals"')
        conn.commit()
    
    # Обновляем запись с типом награды
    cur.execute('UPDATE promo_codes SET reward_type = ? WHERE code = ?', (reward_type, code))
    conn.commit()
    conn.close()
    
    reward_icon = '💎 кристаллов' if reward_type == 'crystals' else '💰 серебра'
    
    keyboard = VkKeyboard()
    keyboard.add_button('📋 Скопировать код', color=VkKeyboardColor.PRIMARY,
                       payload={'cmd': 'copy_code', 'code': code})
    keyboard.add_line()
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    
    text = (
        f"✅ Создан новый промокод!\n\n"
        f"📌 Код: `{code}`\n"
        f"🎁 Награда: {amount} {reward_icon}\n"
        f"⏳ Действует: {days} дней\n"
        f"🔄 Использований: {max_uses}\n"
        f"📝 Описание: {description or 'Нет'}\n\n"
        f"📋 Нажмите кнопку ниже, чтобы скопировать код."
    )
    
    await send_message(vk, user_id, text, keyboard)


async def admin_show_codes(vk, user_id):
    """Показать список всех промокодов"""
    if not await is_admin(user_id):
        await send_message(vk, user_id, '❌ Доступ запрещён. Только для администраторов.')
        return
    
    codes = get_codes_list(limit=20)
    stats = get_codes_stats()
    
    if not codes:
        await send_message(vk, user_id, '📭 Нет созданных промокодов.')
        return
    
    text = f"📊 Статистика промокодов:\n"
    text += f"📌 Всего: {stats['total']}\n"
    text += f"🎁 Всего награждено: {stats['total_amount']}\n"
    text += f"🔄 Всего использований: {stats['total_uses']}\n\n"
    text += "📋 Список промокодов:\n\n"
    
    for code in codes:
        status = "✅ Активен" if code['is_active'] else "❌ Неактивен"
        reward_icon = '💎' if code.get('reward_type', 'crystals') == 'crystals' else '💰'
        text += f"📌 {code['code']}\n"
        text += f"   {reward_icon} {code['amount']} | Использовано: {code['used_count']}/{code['max_uses']}\n"
        text += f"   ⏳ До: {code['expires_at'][:10] if code['expires_at'] else '∞'}\n"
        text += f"   📝 {code['description'] or 'Нет описания'}\n"
        text += f"   📊 {status}\n\n"
    
    keyboard = VkKeyboard()
    keyboard.add_button('🔄 Обновить', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'admin_codes_refresh'})
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'back'})
    
    await send_message(vk, user_id, text, keyboard)


async def admin_codes_menu(vk, user_id):
    """Меню управления промокодами"""
    if not await is_admin(user_id):
        await send_message(vk, user_id, '❌ Доступ запрещён. Только для администраторов.')
        return
    
    keyboard = VkKeyboard()
    keyboard.add_button('💎 Код на 100 кристаллов', color=VkKeyboardColor.PRIMARY, 
                       payload={'cmd': 'admin_code_create', 'amount': 100, 'type': 'crystals'})
    keyboard.add_button('💎 Код на 500 кристаллов', color=VkKeyboardColor.PRIMARY, 
                       payload={'cmd': 'admin_code_create', 'amount': 500, 'type': 'crystals'})
    keyboard.add_line()
    keyboard.add_button('💎 Код на 1000 кристаллов', color=VkKeyboardColor.PRIMARY, 
                       payload={'cmd': 'admin_code_create', 'amount': 1000, 'type': 'crystals'})
    keyboard.add_line()
    keyboard.add_button('💰 Код на 10000 серебра', color=VkKeyboardColor.PRIMARY, 
                       payload={'cmd': 'admin_code_create', 'amount': 10000, 'type': 'silver'})
    keyboard.add_button('💰 Код на 50000 серебра', color=VkKeyboardColor.PRIMARY, 
                       payload={'cmd': 'admin_code_create', 'amount': 50000, 'type': 'silver'})
    keyboard.add_line()
    keyboard.add_button('💰 Код на 100000 серебра', color=VkKeyboardColor.PRIMARY, 
                       payload={'cmd': 'admin_code_create', 'amount': 100000, 'type': 'silver'})
    keyboard.add_line()
    keyboard.add_button('📋 Список кодов', color=VkKeyboardColor.SECONDARY, 
                       payload={'cmd': 'admin_codes_list'})
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'back'})
    
    await send_message(vk, user_id, 
        '🛠️ Управление промокодами\n\n'
        'Выберите тип и сумму награды:', keyboard)