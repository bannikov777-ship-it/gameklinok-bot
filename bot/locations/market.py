# locations/market.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from core import get_character_async, update_user_async, send_message, get_item_prefix, get_consumable_templates, buy_consumable, get_character, get_user_async
from keyboards import get_market_keyboard, get_healer_keyboard, get_back_keyboard
from items import get_item_template_id_by_name, get_item_stats, generate_shop_item, create_player_item_with_rarity
from auction import get_active_auction_lots, expire_and_return_expired, buy_auction_lot
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from .base import navigate_to

MARKET_IMAGE = 'photo-240828623_456239033'
SHOP_IMAGE = 'photo-240828623_456239243'

async def show_market(vk, user_id):
    """Показ рынка"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    text = f"🏪 Рынок – здесь можно купить снаряжение и услуги.\nВаши 💰: {char['silver']}"
    await send_message(vk, user_id, text, get_market_keyboard(), attachment=MARKET_IMAGE)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'city'
    await update_user_async(user_id, state='market', context=context)


async def show_market_shop(vk, user_id):
    """Показ магазина - выбор категории"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    level = char['level']
    shop_level = get_shop_item_level(level)
    class_name = char['class']
    
    # Сохраняем уровень магазина в контексте
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['shop_level'] = shop_level
    await update_user_async(user_id, context=context)
    
    # Создаем клавиатуру с категориями
    keyboard = VkKeyboard()
    keyboard.add_button('⚔️ Оружие', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market_category', 'category': 'weapons'})
    keyboard.add_button('🛡️ Броня', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market_category', 'category': 'armor'})
    keyboard.add_line()
    keyboard.add_button('🎩 Шлемы', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market_category', 'category': 'helmets'})
    keyboard.add_button('👢 Сапоги', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market_category', 'category': 'boots'})
    if class_name and level >= 20:
        keyboard.add_line()
        keyboard.add_button('🛡️ Щиты', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market_category', 'category': 'shields'})
    keyboard.add_line()
    keyboard.add_button('🔙 Назад в рынок', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'back'})
    
    message = f"🏪 Магазин (уровень предметов: {shop_level})\n"
    message += f"⚪ Только обычные предметы (белые)\n"
    message += f"📦 Редкие предметы выпадают с монстров!\n"
    message += f"Ваши 💰: {char['silver']}\n"
    message += f"Ваш уровень: {level}\n\n"
    message += "Выберите категорию товаров:"
    
    await send_message(vk, user_id, message, keyboard, attachment=SHOP_IMAGE)
    await update_user_async(user_id, state='market_shop', context=context)


async def show_market_category(vk, user_id, category):
    """Показ товаров по категории"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    user_data = await get_user_async(user_id)
    context = user_data['context']
    shop_level = context.get('shop_level', 1)
    level = char['level']
    class_name = char['class']
    rarity = 1
    
    # Определяем товары по категории
    categories = {
        'weapons': {
            'items': ['Меч', 'Молот', 'Лук'],
            'slot': 'weapon_right',
            'title': '⚔️ Оружие'
        },
        'armor': {
            'items': ['Кожаная броня', 'Кольчуга', 'Кираса'],
            'slot': 'armor',
            'title': '🛡️ Броня'
        },
        'helmets': {
            'items': ['Подшлемник', 'Шлем', 'Треуголка'],
            'slot': 'head',
            'title': '🎩 Шлемы'
        },
        'boots': {
            'items': ['Кожаные сапоги', 'Железные сапоги', 'Стальные сапоги'],
            'slot': 'boots',
            'title': '👢 Сапоги'
        },
        'shields': {
            'items': ['Щит'],
            'slot': 'weapon_left',
            'title': '🛡️ Щиты'
        }
    }
    
    if category not in categories:
        await show_market_shop(vk, user_id)
        return
    
    cat = categories[category]
    
    # Проверяем доступность щитов
    if category == 'shields' and (not class_name or level < 20):
        await send_message(vk, user_id, '🛡️ Щиты доступны только после выбора класса (20 уровень)', get_back_keyboard('магазин'))
        await show_market_shop(vk, user_id)
        return
    
    keyboard = VkKeyboard()
    price = 100 + shop_level * 250
    
    # Добавляем кнопки с предметами категории
    for item_name in cat['items']:
        template_id = get_item_template_id_by_name(item_name)
        if template_id:
            stats = get_item_stats(template_id, shop_level, rarity, upgrade_level=0)
            if stats:
                attack, defense, hp, mana = stats['attack'], stats['defense'], stats['hp'], stats['mana']
                bonus_crit = stats.get('bonus_crit', 0)
                bonus_dodge = stats.get('bonus_dodge', 0)
            else:
                attack = defense = hp = mana = bonus_crit = bonus_dodge = 0
        else:
            attack = defense = hp = mana = bonus_crit = bonus_dodge = 0
        
        label = f"⚪ {item_name} (ур.{shop_level})"
        if attack: label += f" ⚔️{attack}"
        if defense: label += f" 🛡️{defense}"
        if hp: label += f" ❤️{hp}"
        if mana: label += f" 💧{mana}"
        if bonus_crit: label += f" 💥{bonus_crit:+}%"
        if bonus_dodge: label += f" 💨{bonus_dodge:+}%"
        label += f" - {price}💰"
        
        keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'market_buy_item', 
                                    'template': item_name, 
                                    'price': price, 
                                    'shop_level': shop_level,
                                    'rarity': rarity})
        keyboard.add_line()
    
    keyboard.add_button('🔙 Назад в категории', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'market_shop'})
    
    await send_message(vk, user_id, f"📦 {cat['title']}\n💰 Цена за предмет: {price}💰\nВыберите предмет для покупки:", keyboard)
    await update_user_async(user_id, state='market_category', context=context)


async def show_market_buy_item(vk, user_id, template_name, price, shop_level, rarity):
    """Покупка предмета"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    if char['silver'] < price:
        await send_message(vk, user_id, f'❌ Недостаточно серебра! Нужно {price}💰.', get_back_keyboard('магазин'))
        return
    
    template_id = get_item_template_id_by_name(template_name)
    if not template_id:
        await send_message(vk, user_id, '❌ Ошибка: предмет не найден.', get_back_keyboard('магазин'))
        return
    
    # Создаем предмет
    item_id = create_player_item_with_rarity(char['id'], template_id, shop_level, rarity)
    if not item_id:
        await send_message(vk, user_id, '❌ Ошибка при создании предмета.', get_back_keyboard('магазин'))
        return
    
    # Списываем серебро
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE characters SET silver = silver - ? WHERE id = ?', (price, char['id']))
    conn.commit()
    conn.close()
    
    # Обновляем статы
    from core import recalc_stats_async
    await recalc_stats_async(char['id'])
    
    rarity_names = {1: 'Обычный', 2: 'Необычный', 3: 'Редкий', 4: 'Эпический', 5: 'Легендарный'}
    await send_message(vk, user_id, f'✅ Вы купили **{rarity_names[rarity]} {template_name}** (ур.{shop_level}) за {price}💰!')
    await show_market_shop(vk, user_id)


def get_shop_item_level(player_level):
    """Определение уровня предметов в магазине"""
    if player_level <= 4: return 1
    elif player_level <= 9: return 5
    elif player_level <= 14: return 10
    elif player_level <= 19: return 15
    elif player_level <= 24: return 20
    elif player_level <= 29: return 25
    elif player_level <= 34: return 30
    elif player_level <= 39: return 35
    elif player_level <= 44: return 40
    elif player_level <= 49: return 45
    elif player_level <= 54: return 50
    elif player_level <= 59: return 55
    else: return 60