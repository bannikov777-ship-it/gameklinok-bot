# core/__init__.py
from config import DB_NAME
from .database import init_db
from .character import (
    get_character, get_character_by_id, create_character, 
    get_city, apply_debuff, remove_debuff, update_max_forest_depth, 
    get_item_prefix
)
from .user import get_user, add_user, update_user
from .resources import get_player_resources, add_resource, remove_resource 
from .messaging import send_message
from .stats import recalc_stats, CLASS_BASE_STATS, CLASS_GROWTH, NEUTRAL_STATS, NEUTRAL_GROWTH
from .render import render_profile, render_inventory, upload_profile_image, format_gender
from .async_wrappers import (
    get_user_async, update_user_async, get_character_async, 
    get_character_by_id_async, recalc_stats_async,
    get_player_consumables, get_player_crystals, buy_consumable,
    use_consumable, get_consumable_templates, get_player_herbs,
    add_herb, sell_all_herbs
)

# Импортируем функции из items.py
from items import get_equipped_items, get_player_items, equip_item, unequip_item, generate_shop_item, get_item_stats, get_item_template_id_by_name

# Переименовываем для удобства
get_equipment = get_equipped_items
get_inventory = get_player_items

__all__ = [
    'init_db', 'DB_NAME',
    'get_character', 'get_character_by_id', 'create_character',
    'get_city', 'apply_debuff', 'remove_debuff', 'update_max_forest_depth',
    'get_item_prefix',
    'get_user', 'add_user', 'update_user',
    'send_message',
    'recalc_stats', 'CLASS_BASE_STATS', 'CLASS_GROWTH', 'NEUTRAL_STATS', 'NEUTRAL_GROWTH',
    'render_profile', 'render_inventory', 'upload_profile_image', 'format_gender',
    'get_user_async', 'update_user_async', 'get_character_async',
    'get_character_by_id_async', 'recalc_stats_async',
    'get_player_consumables', 'get_player_crystals', 'buy_consumable',
    'use_consumable', 'get_consumable_templates', 'get_player_herbs',
    'add_herb', 'sell_all_herbs',
    'get_equipment', 'get_inventory', 'equip_item', 'unequip_item',
    'generate_shop_item', 'get_item_stats', 'get_item_template_id_by_name',
    'get_player_resources', 'add_resource', 'remove_resource' 
]