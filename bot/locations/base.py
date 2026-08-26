# locations/base.py
from core import get_character_async, update_user_async, send_message, get_user_async
from keyboards import get_back_keyboard
import asyncio
import random

# Базовые изображения локаций
FOREST_IMAGE = 'photo-240828623_456239316'
FOREST_DEEP_IMAGE = 'photo-240828623_456239315'
FOREST_WANDER_IMAGE = 'photo-240828623_456239317'
FOREST_EXIT_IMAGE = 'photo-240828623_456239316'

GRAVEYARD_IMAGE = 'photo-240828623_456239323'
GRAVEYARD_DEEP_IMAGE = 'photo-240828623_456239322'
GRAVEYARD_WANDER_IMAGE = 'photo-240828623_456239321'

MEADOW_IMAGE = 'photo-240828623_456239318'
TOWER_IMAGE = 'photo-240828623_456239325'

# Словарь задержек для переходов между локациями (в секундах)
NAVIGATION_DELAYS = {
    'city': 1.0,           # Город
    'exit': 3.0,           # Выход из города
    'meadow': 2.5,         # Луг (среднее)
    'forest': 2.0,         # Лес
    'graveyard': 2.5,      # Кладбище
    'tower': 2.0,          # Башня
    'market': 1.0,         # Рынок
    'tavern': 1.0,         # Таверна
    'guild': 1.0,          # Гильдия
    'church': 1.0,         # Собор
    'healer': 1.0,         # Лекарь
    'smithy': 1.0,         # Кузница
    'auction': 1.0,        # Аукцион
    'hunters': 1.0,        # Гильдия охотников
    'town_hall': 1.0,      # Ратуша
    'profile': 1.0,        # Профиль
    'inventory': 1.0,      # Инвентарь
    'premium_shop': 1.0,   # Премиум магазин
    'admin_panel': 1.0,    # Админ-панель
}

async def delay_navigation(vk, user_id, target_state):
    """
    Задержка перед навигацией с отправкой статуса
    """
    # Определяем задержку
    if target_state == 'exit':
        delay = 3.0
        message = "🚪 Вы выходите за городские ворота..."
    elif target_state == 'meadow':
        delay = random.uniform(2.0, 5.0)  # 2-5 секунд
        message = "🌿 Вы идёте по тропинке к лугу..."
    elif target_state == 'forest':
        delay = 2.0
        message = "🌲 Вы входите в лес..."
    elif target_state == 'graveyard':
        delay = 2.5
        message = "🪦 Вы приближаетесь к кладбищу..."
    elif target_state == 'tower':
        delay = 2.0
        message = "🗼 Вы направляетесь к Башне..."
    elif target_state == 'city':
        delay = 1.0
        message = "🏙️ Вы возвращаетесь в город..."
    else:
        delay = 1.0
        message = None
    
    # Отправляем сообщение если есть
    if message:
        await send_message(vk, user_id, message)
    
    # Задержка
    await asyncio.sleep(delay)


async def navigate_to(vk, user_id, target_state):
    """Навигация по локациям с задержкой"""
    from locations.city import show_city, show_city2
    from locations.exit import show_exit
    from locations.forest import show_forest
    from locations.graveyard import show_graveyard
    from locations.meadow import show_meadow
    from locations.tower import show_tower
    from locations.tavern import show_tavern
    from locations.town_hall import show_town_hall
    from locations.guild import show_guild
    from locations.market import show_market
    from locations.hunters import show_hunters
    from locations.church import show_church
    from locations.profile import show_profile
    from locations.inventory import show_inventory
    from locations.healer import show_healer
    from locations.smithy import show_smithy
    from locations.auction import show_auction
    from locations.premium import show_premium_shop
    
    # Применяем задержку перед навигацией
    await delay_navigation(vk, user_id, target_state)
    
    # Переходим в нужную локацию
    if target_state == 'city':
        await show_city(vk, user_id)
    elif target_state == 'city2':
        await show_city2(vk, user_id)
    elif target_state == 'exit':
        await show_exit(vk, user_id)
    elif target_state == 'forest':
        await show_forest(vk, user_id)
    elif target_state == 'graveyard':
        await show_graveyard(vk, user_id)
    elif target_state == 'meadow':
        await show_meadow(vk, user_id)
    elif target_state == 'tower_path':
        await show_tower(vk, user_id)
    elif target_state == 'tavern':
        await show_tavern(vk, user_id)
    elif target_state == 'town_hall':
        await show_town_hall(vk, user_id)
    elif target_state == 'guild':
        await show_guild(vk, user_id)
    elif target_state == 'market':
        await show_market(vk, user_id)
    elif target_state == 'hunters':
        await show_hunters(vk, user_id)
    elif target_state == 'church':
        await show_church(vk, user_id)
    elif target_state == 'profile':
        await show_profile(vk, user_id)
    elif target_state == 'inventory':
        await show_inventory(vk, user_id)
    elif target_state == 'healer':
        await show_healer(vk, user_id)
    elif target_state == 'smithy':
        await show_smithy(vk, user_id)
    elif target_state == 'auction':
        await show_auction(vk, user_id)
    elif target_state == 'premium_shop':
        await show_premium_shop(vk, user_id)
    else:
        await show_city(vk, user_id)