# locations/tavern.py
from core import get_character_async, update_user_async, send_message, get_user_async
from keyboards import get_back_keyboard
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from scheduler import scheduler
import time
import sqlite3
from config import DB_NAME

TAVERN_IMAGE = 'photo-240828623_456239032'

def get_tavern_keyboard():
    """Клавиатура таверны - 2 ряда"""
    from vk_api.keyboard import VkKeyboard, VkKeyboardColor
    keyboard = VkKeyboard()
    
    # Первый ряд - 2 кнопки
    keyboard.add_button('🍽️ Поесть', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'tavern_food'})
    keyboard.add_button('😴 Снять комнату', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'tavern_room'})
    keyboard.add_line()
    
    # Второй ряд - 2 кнопки
    keyboard.add_button('📜 Квесты', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'tavern_quests'})
    keyboard.add_button('🗣️ Слухи', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'tavern_rumors'})
    keyboard.add_line()
    
    # Третий ряд - 1 кнопка (назад в город)
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    
    return keyboard

def get_food_keyboard():
    """Клавиатура меню еды - каждая кнопка на новой строке"""
    from vk_api.keyboard import VkKeyboard, VkKeyboardColor
    keyboard = VkKeyboard()
    
    food_items = [
        ('🍞 Хлеб (+10% HP)', 10, 10),
        ('🍖 Мясо (+25% HP)', 25, 30),
        ('🍲 Суп (+40% HP)', 40, 60),
        ('🐟 Рыба (+50% HP)', 50, 80),
        ('🥩 Стейк (+75% HP)', 75, 120),
        ('🍗 Жаркое (+100% HP)', 100, 200),
    ]
    
    for name, percent, price in food_items:
        keyboard.add_button(
            f'{name} ({price}💰)',
            color=VkKeyboardColor.PRIMARY,
            payload={'cmd': 'buy_food', 'percent': percent, 'price': price}
        )
        keyboard.add_line()
    
    keyboard.add_button('🍺 В таверну', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_tavern'})
    
    return keyboard

def get_sleep_keyboard():
    """Клавиатура выбора комнаты - каждая кнопка на новой строке"""
    from vk_api.keyboard import VkKeyboard, VkKeyboardColor
    keyboard = VkKeyboard()
    
    rooms = [
        ('🛏️ Простая (2ч, +30%)', 2, 30, 50),
        ('🛏️ Уютная (4ч, +60%)', 4, 60, 100),
        ('🛏️ Люкс (6ч, +100%)', 6, 100, 200),
    ]
    
    for name, hours, percent, price in rooms:
        keyboard.add_button(
            f'{name} ({price}💰)',
            color=VkKeyboardColor.PRIMARY,
            payload={'cmd': 'sleep', 'hours': hours, 'percent': percent, 'price': price}
        )
        keyboard.add_line()
    
    keyboard.add_button('🍺 В таверну', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_tavern'})
    
    return keyboard

def get_sleep_status_keyboard():
    """Клавиатура статуса сна"""
    from vk_api.keyboard import VkKeyboard, VkKeyboardColor
    keyboard = VkKeyboard()
    
    keyboard.add_button('🔄 Проверить', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'sleep_check'})
    keyboard.add_button('❌ Проснуться', color=VkKeyboardColor.NEGATIVE, payload={'cmd': 'sleep_cancel'})
    keyboard.add_line()
    
    keyboard.add_button('🍺 В таверну', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_tavern'})
    
    return keyboard

async def show_tavern(vk, user_id):
    """Показ таверны"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    text = f"🍺 Таверна «Пьяный тролль»\n\nВаши 💰: {char['silver']}\nВаше ❤️: {char['hp']}/{char['max_hp']}\n\nЧто желаешь?"
    
    await send_message(vk, user_id, text, get_tavern_keyboard(), attachment=TAVERN_IMAGE)
    
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'city'
    await update_user_async(user_id, state='tavern', context=context)

async def show_tavern_food(vk, user_id):
    """Показ меню еды"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    text = f"🍖 Выберите еду:\n\nВаши 💰: {char['silver']}\nВаше ❤️: {char['hp']}/{char['max_hp']}"
    
    await send_message(vk, user_id, text, get_food_keyboard())
    
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'tavern'
    await update_user_async(user_id, state='tavern_food', context=context)

async def show_tavern_room(vk, user_id):
    """Показ комнаты"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    text = f"🛏 Выберите комнату:\n\nВаши 💰: {char['silver']}"
    
    await send_message(vk, user_id, text, get_sleep_keyboard())
    
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'tavern'
    await update_user_async(user_id, state='tavern_room', context=context)

async def restore_after_sleep(vk, user_id, percent):
    """Восстановление после сна"""
    char = await get_character_async(user_id)
    if not char:
        return
    
    max_hp = char['max_hp']
    max_mana = char['max_mana']
    max_stamina = char['max_stamina']
    
    restore_hp = int(max_hp * percent / 100)
    restore_mana = int(max_mana * percent / 100)
    restore_stamina = int(max_stamina * percent / 100)
    
    new_hp = min(max_hp, char['hp'] + restore_hp)
    new_mana = min(max_mana, char['mana'] + restore_mana)
    new_stamina = min(max_stamina, char['stamina'] + restore_stamina)
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE characters SET hp = ?, mana = ?, stamina = ? WHERE id = ?', 
                (new_hp, new_mana, new_stamina, char['id']))
    conn.commit()
    conn.close()
    
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context.pop('sleep_task_id', None)
    context.pop('sleep_end_time', None)
    await update_user_async(user_id, context=context)
    
    await send_message(vk, user_id,
        f'😴 Просыпайтесь! Вы восстановили:\n❤️ {restore_hp} HP\n💧 {restore_mana} MP\n⚡ {restore_stamina} Stamina',
        get_back_keyboard('таверну'))
    await show_tavern(vk, user_id)