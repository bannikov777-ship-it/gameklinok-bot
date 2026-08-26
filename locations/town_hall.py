# locations/town_hall.py
from core import get_character_async, update_user_async, send_message, get_user_async
from keyboards import get_town_hall_keyboard, get_class_choice_keyboard, get_back_keyboard

TOWN_HALL_IMAGE = 'photo-240828623_456239029'
RATING_IMAGE = 'photo-240828623_456239333'

async def show_town_hall(vk, user_id):
    """Показ ратуши"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    await send_message(vk, user_id, '🏛 Ратуша – центр управления городом. Что вас интересует?', 
                      get_town_hall_keyboard(char), attachment=TOWN_HALL_IMAGE)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'city'
    await update_user_async(user_id, state='town_hall', context=context)

async def show_rating(vk, user_id):
    """Показ рейтинга"""
    import sqlite3
    from core import DB_NAME, format_gender
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT name, gender, class, level, max_forest_depth
        FROM characters
        ORDER BY level DESC, max_forest_depth DESC
        LIMIT 10
    ''')
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await send_message(vk, user_id, 'Пока нет данных для рейтинга.', get_back_keyboard('ратушу'), attachment=RATING_IMAGE)
        return
    lines = ["📊 Рейтинг игроков:\n"]
    for i, row in enumerate(rows, 1):
        name, gender, class_, level, depth = row
        class_display = class_ if class_ else "Не выбран"
        gender_display = format_gender(gender)
        lines.append(f"{i}. {name} | {gender_display} | {class_display} | Ур.{level} | Глубина: {depth}")
    message = "\n".join(lines)
    await send_message(vk, user_id, message, get_back_keyboard('ратушу'), attachment=RATING_IMAGE)