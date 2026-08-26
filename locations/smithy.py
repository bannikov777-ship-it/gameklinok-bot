# locations/smithy.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from core import get_character_async, update_user_async, send_message, get_player_crystals, get_character, get_user_async, DB_NAME
from keyboards import get_back_keyboard
from items import get_equipped_items, upgrade_item
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

SMITHY_IMAGE = 'photo-240828623_456239244'

async def show_smithy(vk, user_id):
    """Показ кузницы"""
    try:
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        equipment = get_equipped_items(char['id'])
        upgradable = [item for item in equipment.values() if item['upgrade_level'] < 10]
        if not upgradable:
            await send_message(vk, user_id, 'У вас нет предметов для улучшения (макс +10).', get_back_keyboard('рынок'), attachment=SMITHY_IMAGE)
            return
        keyboard = VkKeyboard()
        for item in upgradable:
            rarity_price = {1: 250, 2: 350, 3: 550, 4: 750, 5: 1250}.get(item['rarity'], 250)
            price = 100 + rarity_price * item['upgrade_level']
            label = f"{item['name']} (+{item['upgrade_level']}) — {price}💰"
            keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                                payload={'cmd': 'smithy_select_item', 'item_id': item['id']})
            keyboard.add_line()
        keyboard.add_button('🏪 На рынок', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_market'})
        await send_message(vk, user_id, f"⚒ Кузница\nВаши 💰: {char['silver']}\nВыберите предмет для улучшения:", keyboard, attachment=SMITHY_IMAGE)
        user_data = await get_user_async(user_id)
        context = user_data['context']
        context['parent_state'] = 'market'
        await update_user_async(user_id, state='smithy', context=context)
    except Exception as e:
        print(f"❌ Ошибка в show_smithy: {e}")
        import traceback
        traceback.print_exc()
        await send_message(vk, user_id, f'⚠️ Ошибка в кузнице: {e}', get_back_keyboard('рынок'))

async def show_smithy_upgrade_menu(vk, user_id, item_id):
    """Меню улучшения предмета"""
    try:
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        equipment = get_equipped_items(char['id'])
        item = None
        for eq_item in equipment.values():
            if eq_item['id'] == item_id:
                item = eq_item
                break
        if not item:
            await send_message(vk, user_id, 'Предмет не найден.', get_back_keyboard('кузница'))
            return
        upgrade_level = item['upgrade_level']
        if upgrade_level >= 10:
            await send_message(vk, user_id, 'Этот предмет уже имеет максимальный уровень заточки (+10).', get_back_keyboard('кузница'))
            return
        if upgrade_level < 3:
            base_chance = 100
        else:
            base_chance = 100 - (upgrade_level - 2) * 10
        rarity_price = {1: 250, 2: 350, 3: 550, 4: 750, 5: 1250}.get(item['rarity'], 250)
        price = 100 + rarity_price * upgrade_level
        crystals = get_player_crystals(char['id'])
        keyboard = VkKeyboard()
        keyboard.add_button(f'🔨 Заточить (шанс {base_chance}%, {price}💰)', color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'smithy_upgrade', 'crystal_id': None})
        keyboard.add_line()
        for c in crystals:
            bonus = c['bonus']
            total_chance = min(100, base_chance + bonus)
            label = f"{c['icon']} {c['name']} (x{c['quantity']}) → шанс {total_chance}%"
            keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                                payload={'cmd': 'smithy_upgrade', 'crystal_id': c['id']})
            keyboard.add_line()
        keyboard.add_button('🔙 Назад к списку', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'smithy'})
        await send_message(vk, user_id,
            f"⚒ Улучшение: {item['name']} (+{upgrade_level})\n"
            f"Цена: {price}💰\n"
            f"Базовый шанс: {base_chance}%\n"
            f"Выберите кристалл или точите без него:",
            keyboard)
        user_data = await get_user_async(user_id)
        context = user_data['context']
        context['smithy_item_id'] = item_id
        await update_user_async(user_id, state='smithy_upgrade', context=context)
    except Exception as e:
        print(f"❌ Ошибка в show_smithy_upgrade_menu: {e}")
        import traceback
        traceback.print_exc()
        await send_message(vk, user_id, f'⚠️ Ошибка: {e}', get_back_keyboard('кузница'))