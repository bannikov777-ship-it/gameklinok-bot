# locations/meadow.py
import random
import sqlite3
import asyncio
from core import get_character_async, update_user_async, send_message, add_herb, DB_NAME, get_user_async
from keyboards import get_meadow_keyboard, get_back_keyboard
from .base import MEADOW_IMAGE, TOWER_IMAGE

MEADOW_IMAGE = 'photo-240828623_456239318'
MEADOW_HERBS_IMAGE = 'photo-240828623_456239320'

async def show_meadow(vk, user_id):
    """Показ луга"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    await send_message(vk, user_id, '🌿 Вы на зелёном лугу. Слышен стрекот кузнечиков, вдалеке виднеется башня. Что будем делать?', 
                       get_meadow_keyboard(), attachment=MEADOW_IMAGE)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'exit'
    await update_user_async(user_id, state='meadow', context=context)

async def meadow_herbs(vk, user_id):
    """Сбор трав на лугу"""
    # Сначала показываем картинку и сообщение о начале сбора
    await send_message(vk, user_id, "🌿 Вы начинаете собирать травы...", attachment=MEADOW_HERBS_IMAGE)
    
    # Задержка 3-8 секунд
    await asyncio.sleep(random.randint(3, 8))
    
    # После задержки определяем результат
    herbs = ['Зверобой', 'Мелисса', 'Полынь', 'Крапива', 'Лаванда', 'Тысячелистник', 'Ромашка', 'Чабрец']
    herb = random.choice(herbs)
    count = random.randint(1, 3)
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_meadow_keyboard())
        return
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('SELECT id FROM herbs WHERE name = ?', (herb,))
        row = cur.fetchone()
        conn.close()
        if row:
            herb_id = row[0]
            add_herb(char['id'], herb_id, count)
            await send_message(vk, user_id, f'🌿 Вы собрали {herb} x{count}! Они добавлены в ваш инвентарь.', get_meadow_keyboard())
        else:
            await send_message(vk, user_id, '❌ Ошибка: трава не найдена.', get_meadow_keyboard())
    except Exception as e:
        await send_message(vk, user_id, f'❌ Ошибка при сборе трав: {e}', get_meadow_keyboard())