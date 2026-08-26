# locations/church.py
from core import get_character_async, update_user_async, send_message, remove_debuff, recalc_stats_async, get_user_async
from keyboards import get_church_keyboard, get_back_keyboard

CHURCH_IMAGE = 'photo-240828623_456239035'

async def show_church(vk, user_id):
    """Показ собора"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    text = f"⛪ Собор\nВаши 💰: {char['silver']}\n\n"
    if char.get('debuff') == 1:
        text += "☠️ На вас наложено Проклятие (-30% к статам).\nСнимите его за 1000💰."
    elif char.get('debuff') == 2:
        text += "🔥 На вас наложена Печать башни (-50% к статам).\nСнимите её за 3000💰."
    else:
        text += "Вы чувствуете благодать. Проклятий нет."
    keyboard = get_church_keyboard(char)
    await send_message(vk, user_id, text, keyboard, attachment=CHURCH_IMAGE)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'city'
    await update_user_async(user_id, state='church', context=context)

async def show_church_remove_debuff(vk, user_id, debuff_level=1):
    """Снятие проклятия"""
    import sqlite3
    from core import DB_NAME
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    if char.get('debuff') != debuff_level:
        await send_message(vk, user_id, 'На вас нет такого проклятия.', get_back_keyboard('собор'))
        return
    price = 1000 if debuff_level == 1 else 3000
    if char['silver'] < price:
        await send_message(vk, user_id, f'❌ Недостаточно серебра! Нужно {price}💰.', get_back_keyboard('собор'))
        return
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE characters SET silver = silver - ?, debuff = 0 WHERE id = ?', (price, char['id']))
    conn.commit()
    conn.close()
    await recalc_stats_async(char['id'])
    await send_message(vk, user_id, f'✅ Проклятие снято! Статы восстановлены.', get_back_keyboard('собор'))
    await show_church(vk, user_id)