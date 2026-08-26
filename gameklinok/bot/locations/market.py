# locations/market.py (полный исправленный)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import random
from core import get_character_async, update_user_async, send_message, get_item_prefix, get_consumable_templates, buy_consumable, get_character, get_user_async
from keyboards import get_market_keyboard, get_healer_keyboard, get_back_keyboard
from items import get_item_template_id_by_name, get_item_stats, generate_shop_item, create_player_item_with_rarity
from auction import get_active_auction_lots, expire_and_return_expired, buy_auction_lot
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from .base import navigate_to
from config import DB_NAME

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
    
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['shop_level'] = shop_level
    await update_user_async(user_id, context=context)
    
    keyboard = VkKeyboard()
    keyboard.add_button('🗡️ Оружие', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market_category', 'category': 'weapons'})
    keyboard.add_button('🛡️ Броня', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market_category', 'category': 'armor'})
    keyboard.add_line()
    keyboard.add_button('🎩 Шлемы', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market_category', 'category': 'helmets'})
    keyboard.add_button('👢 Сапоги', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market_category', 'category': 'boots'})
    if class_name and level >= 20:
        keyboard.add_line()
        keyboard.add_button('🛡️ Щиты', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market_category', 'category': 'shields'})
    keyboard.add_line()
    keyboard.add_button('🏪 На рынок', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_market'})
    
    message = f"🏪 Магазин (уровень предметов: {shop_level})\n"
    message += f"⚪ Только обычные предметы (белые)\n"
    message += f"📦 Редкие предметы выпадают с монстров!\n"
    message += f"Ваши 💰: {char['silver']}\n"
    message += f"Ваш уровень: {level}\n\n"
    message += "Выберите категорию товаров:"
    
    await send_message(vk, user_id, message, keyboard, attachment=SHOP_IMAGE)
    await update_user_async(user_id, state='market_shop', context=context)


async def show_market_category(vk, user_id, category):
    """Показ товаров по категории с характеристиками на кнопках"""
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
    
    # СОХРАНЯЕМ ТЕКУЩУЮ КАТЕГОРИЮ
    context['last_category'] = category
    await update_user_async(user_id, context=context)
    
    categories = {
        'weapons': {
            'items': ['Меч', 'Молот', 'Лук'],
            'slot': 'weapon_right',
            'title': '🗡️ Оружие'
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
    
    if category == 'shields' and (not class_name or level < 20):
        await send_message(vk, user_id, '🛡️ Щиты доступны только после выбора класса (20 уровень)', get_back_keyboard('магазин'))
        await show_market_shop(vk, user_id)
        return
    
    keyboard = VkKeyboard()
    price = 100 + shop_level * 250
    
    for item_name in cat['items']:
        template_id = get_item_template_id_by_name(item_name)
        if not template_id:
            continue
        
        stats = get_item_stats(template_id, shop_level, rarity, upgrade_level=0)
        
        # Формируем текст кнопки с характеристиками
        stats_parts = []
        if stats and stats.get('attack', 0) > 0:
            stats_parts.append(f"⚔+{stats['attack']}")
        if stats and stats.get('defense', 0) > 0:
            stats_parts.append(f"🛡+{stats['defense']}")
        if stats and stats.get('hp', 0) > 0:
            stats_parts.append(f"❤️+{stats['hp']}")
        if stats and stats.get('mana', 0) > 0:
            stats_parts.append(f"💧+{stats['mana']}")
        if stats and stats.get('bonus_crit', 0) != 0:
            crit = stats['bonus_crit']
            stats_parts.append(f"💥{crit:+}%")
        if stats and stats.get('bonus_dodge', 0) != 0:
            dodge = stats['bonus_dodge']
            stats_parts.append(f"💨{dodge:+}%")
        
        icon = stats['icon'] if stats else '📦'
        
        # Формируем кнопку
        if stats_parts:
            # Ограничиваем количество характеристик на кнопке (макс 4)
            if len(stats_parts) > 4:
                stats_parts = stats_parts[:4]
            label = f"{icon} {item_name} ({', '.join(stats_parts)})"
        else:
            label = f"{icon} {item_name}"
        
        # Добавляем цену в конец
        label = f"{label} {price}💰"
        
        # Ограничиваем длину кнопки (VK ~40 символов)
        if len(label) > 40:
            # Сокращаем название
            short_name = item_name[:8] + "…" if len(item_name) > 8 else item_name
            if stats_parts:
                label = f"{icon} {short_name} ({', '.join(stats_parts[:2])}) {price}💰"
            else:
                label = f"{icon} {short_name} {price}💰"
            # Если всё ещё длинно, сокращаем ещё
            if len(label) > 40:
                label = label[:37] + "..."
        
        keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'market_buy_item', 
                                    'template': item_name, 
                                    'price': price, 
                                    'shop_level': shop_level,
                                    'rarity': rarity})
        keyboard.add_line()
    
    keyboard.add_button('📦 Назад в категории', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'market_shop'})
    
    await send_message(vk, user_id, f"📦 {cat['title']}\n💰 Цена: {price}💰\nВыберите предмет:", keyboard)
    await update_user_async(user_id, state='market_category', context=context)


async def show_market_buy_item(vk, user_id, template_name, price, shop_level, rarity):
    """Подтверждение покупки предмета с подробными характеристиками"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    if char['silver'] < price:
        await send_message(vk, user_id, f'❌ Недостаточно серебра! Нужно {price}💰.', get_back_keyboard('магазин'))
        # Возвращаемся в категорию
        user_data = await get_user_async(user_id)
        context = user_data['context']
        category = context.get('last_category', 'weapons')
        await show_market_category(vk, user_id, category)
        return
    
    template_id = get_item_template_id_by_name(template_name)
    if not template_id:
        await send_message(vk, user_id, '❌ Ошибка: предмет не найден.', get_back_keyboard('магазин'))
        user_data = await get_user_async(user_id)
        context = user_data['context']
        category = context.get('last_category', 'weapons')
        await show_market_category(vk, user_id, category)
        return
    
    stats = get_item_stats(template_id, shop_level, rarity, upgrade_level=0)
    if not stats:
        await send_message(vk, user_id, '❌ Ошибка получения характеристик.', get_back_keyboard('магазин'))
        user_data = await get_user_async(user_id)
        context = user_data['context']
        category = context.get('last_category', 'weapons')
        await show_market_category(vk, user_id, category)
        return
    
    # Формируем подробное описание предмета
    text = f"🛒 Подтвердите покупку:\n\n"
    text += f"📌 {stats['icon']} {template_name}\n"
    text += f"📊 Уровень: {shop_level}\n"
    text += f"⭐ Редкость: ⚪ Обычный\n\n"
    
    text += "📈 Характеристики:\n"
    if stats.get('attack', 0) > 0:
        text += f"  ⚔️ Атака: +{stats['attack']}\n"
    if stats.get('defense', 0) > 0:
        text += f"  🛡️ Защита: +{stats['defense']}\n"
    if stats.get('hp', 0) > 0:
        text += f"  ❤️ HP: +{stats['hp']}\n"
    if stats.get('mana', 0) > 0:
        text += f"  💧 Мана: +{stats['mana']}\n"
    if stats.get('bonus_crit', 0) != 0:
        crit = stats['bonus_crit']
        text += f"  💥 Крит: {crit:+}%\n"
    if stats.get('bonus_dodge', 0) != 0:
        dodge = stats['bonus_dodge']
        text += f"  💨 Уворот: {dodge:+}%\n"
    
    text += f"\n💰 Цена: {price} серебра\n"
    text += f"💳 Ваше серебро: {char['silver']}\n"
    
    keyboard = VkKeyboard()
    keyboard.add_button('✅ Купить', color=VkKeyboardColor.POSITIVE,
                       payload={'cmd': 'market_buy_confirm', 
                               'template': template_name, 
                               'price': price,
                               'shop_level': shop_level,
                               'rarity': rarity})
    keyboard.add_button('❌ Отмена', color=VkKeyboardColor.NEGATIVE,
                       payload={'cmd': 'back'})
    
    await send_message(vk, user_id, text, keyboard)
    await update_user_async(user_id, state='market_buy_confirm', context={'parent_state': 'market_category'})


async def show_market_buy_execute(vk, user_id, template_name, price, shop_level, rarity):
    """Выполнение покупки предмета"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    # Проверяем достаточно ли серебра
    if char['silver'] < price:
        await send_message(vk, user_id, f'❌ Недостаточно серебра! Нужно {price}💰.', get_back_keyboard('рынок'))
        # Возвращаемся в категорию
        user_data = await get_user_async(user_id)
        context = user_data['context']
        category = context.get('last_category', 'weapons')
        await show_market_category(vk, user_id, category)
        return
    
    # Создаём предмет
    template_id = get_item_template_id_by_name(template_name)
    if not template_id:
        await send_message(vk, user_id, '❌ Предмет не найден.', get_back_keyboard('рынок'))
        user_data = await get_user_async(user_id)
        context = user_data['context']
        category = context.get('last_category', 'weapons')
        await show_market_category(vk, user_id, category)
        return
    
    # Создаём предмет в инвентаре
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Списываем серебро
    cur.execute('UPDATE characters SET silver = silver - ? WHERE id = ?', (price, char['id']))
    
    # Добавляем предмет
    cur.execute('''
        INSERT INTO player_items (owner_id, template_id, level, rarity, upgrade_level, quantity)
        VALUES (?, ?, ?, ?, ?, 1)
    ''', (char['id'], template_id, shop_level, rarity, 0))
    
    conn.commit()
    conn.close()
    
    # Пересчитываем статы
    from core import recalc_stats_async
    await recalc_stats_async(char['id'])
    
    rarity_names = {1: 'Обычный', 2: 'Необычный', 3: 'Редкий', 4: 'Эпический', 5: 'Легендарный'}
    await send_message(vk, user_id, f'✅ Вы купили **{rarity_names[rarity]} {template_name}** (ур.{shop_level}) за {price}💰!\n\nПредмет добавлен в инвентарь.', get_back_keyboard('рынок'))
    
    # Возвращаемся в ту же категорию
    user_data = await get_user_async(user_id)
    context = user_data['context']
    category = context.get('last_category', 'weapons')
    await show_market_category(vk, user_id, category)


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