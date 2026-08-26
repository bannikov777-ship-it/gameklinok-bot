# locations/meadow.py
import random
import sqlite3
import asyncio
from core import get_character_async, update_user_async, send_message, add_herb, DB_NAME, get_user_async
from keyboards import get_meadow_keyboard, get_back_keyboard
from .base import MEADOW_IMAGE, TOWER_IMAGE
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

MEADOW_IMAGE = 'photo-240828623_456239318'
MEADOW_HERBS_IMAGE = 'photo-240828623_456239320'

gathering_state = {}

def get_meadow_keyboard():
    """Клавиатура луга"""
    keyboard = VkKeyboard()
    keyboard.add_button('🌿 Собрать травы', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'meadow_herbs'})
    keyboard.add_button('🗼 Путь к башне', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'meadow_tower'})
    keyboard.add_line()
    keyboard.add_button('🚪 К воротам', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_exit'})
    keyboard.add_button('🏙️ Озерный край', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'meadow_city'})
    return keyboard

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
    """Сбор трав на лугу с блокировкой повторных кликов"""
    if user_id in gathering_state and gathering_state[user_id].get('active', False):
        await send_message(vk, user_id, "⏳ Вы уже собираете травы! Подождите немного...")
        return
    
    task = asyncio.create_task(_do_herb_gathering(vk, user_id))
    gathering_state[user_id] = {'active': True, 'task': task}
    task.add_done_callback(lambda t: _cleanup_gathering(user_id))

async def _do_herb_gathering(vk, user_id):
    """Внутренняя функция сбора трав"""
    try:
        await send_message(vk, user_id, "🌿 Вы начинаете собирать травы...", attachment=MEADOW_HERBS_IMAGE)
        await asyncio.sleep(random.randint(3, 8))
        
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_meadow_keyboard())
            return
        
        herbs = ['Зверобой', 'Мелисса', 'Полынь', 'Крапива', 'Лаванда', 'Тысячелистник', 'Ромашка', 'Чабрец']
        herb = random.choice(herbs)
        count = random.randint(1, 3)
        
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
            
    except asyncio.CancelledError:
        await send_message(vk, user_id, "❌ Сбор трав отменён.")
    except Exception as e:
        await send_message(vk, user_id, f'❌ Ошибка при сборе трав: {e}', get_meadow_keyboard())
    finally:
        _cleanup_gathering(user_id)

def _cleanup_gathering(user_id):
    """Очистка состояния сбора для пользователя"""
    if user_id in gathering_state:
        gathering_state[user_id]['active'] = False