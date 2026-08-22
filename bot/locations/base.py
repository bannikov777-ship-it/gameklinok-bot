# locations/base.py
from core import get_character_async, update_user_async, send_message, get_user_async
from keyboards import get_back_keyboard

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

async def navigate_to(vk, user_id, target_state):
    """Навигация по локациям"""
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
    else:
        await show_city(vk, user_id)