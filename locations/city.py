# locations/city.py
from core import get_character_async, update_user_async, send_message, get_user_async, get_city
from mail import get_unread_mail_count
from keyboards import get_city_keyboard, get_lore_keyboard, get_city2_keyboard, get_back_keyboard
from .base import navigate_to
from admin import is_admin
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

LOR_TEXT = (
    "🌍 Добро пожаловать в мир «Вольного Клинка»!\n\n"
    "Мир расколот на Семь Анклавов — города-государства, каждый из которых выживает благодаря своему ресурсу. "
    "Между ними — Осколочные Пустоши, кишащие монстрами и аномалиями.\n\n"
    "Ты — Искатель, наёмник, которому суждено войти в легенду. Твоя цель — прокачать своего героя, вступить в гильдию, "
    "выполнять опасные миссии и, наконец, штурмовать мистические Башни, скрывающие древнюю силу.\n\n"
    "С чего начнёшь?"
)

CITY_IMAGE = 'photo-240828623_456239022'

async def show_city(vk, user_id):
    """Показ города"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, LOR_TEXT, get_lore_keyboard(), attachment=CITY_IMAGE)
        return
    city_id = char.get('current_city', 1)
    city = get_city(city_id)
    if not city:
        city = get_city(1)
    text = f"🏘️ {city['name']}\n\n{city['description']}"
    
    # Проверяем, является ли пользователь администратором для показа доп. кнопки
    keyboard = get_city_keyboard()
    
    if await is_admin(user_id):
        # Добавляем админ-кнопку в существующую клавиатуру
        keyboard.add_line()
        keyboard.add_button('🛠️ Админ-панель', color=VkKeyboardColor.NEGATIVE, payload={'cmd': 'admin_codes_menu'})
    
    await send_message(vk, user_id, text, keyboard, attachment=city['image_attachment'])
    await update_user_async(user_id, state='city', context={})
    unread = get_unread_mail_count(char['id'])
    if unread > 0:
        await send_message(vk, user_id, f"📬 У вас {unread} непрочитанных писем! Проверьте почту в профиле.")

async def show_city2(vk, user_id):
    """Показ второго города"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    city = get_city(2)
    if not city:
        await send_message(vk, user_id, '❌ Город ещё не доступен.', get_back_keyboard('луг'))
        return
    text = f"🏘️ {city['name']}\n\n{city['description']}"
    
    # Проверяем админа для второго города
    keyboard = get_city2_keyboard()
    
    if await is_admin(user_id):
        keyboard.add_line()
        keyboard.add_button('🛠️ Админ-панель', color=VkKeyboardColor.NEGATIVE, payload={'cmd': 'admin_codes_menu'})
    
    await send_message(vk, user_id, text, keyboard, attachment=city['image_attachment'])
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'meadow'
    await update_user_async(user_id, state='city2', context=context)