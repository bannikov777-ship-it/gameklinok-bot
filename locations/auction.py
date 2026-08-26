# locations/auction.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import sqlite3
from core import (
    get_character_async, update_user_async, send_message, get_user_async,
    get_player_consumables
)
from auction import get_active_auction_lots, expire_and_return_expired, get_lot_by_id, create_auction_lot
from keyboards import get_auction_keyboard, get_back_keyboard
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from items import get_player_items
from config import DB_NAME

async def show_auction(vk, user_id, page=0):
    """Показ аукциона"""
    try:
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        await asyncio.to_thread(expire_and_return_expired)
        lots = await asyncio.to_thread(get_active_auction_lots, 10, page*10)
        if not lots:
            await send_message(vk, user_id, '📭 На аукционе пока нет лотов.', get_auction_keyboard())
            return
        text = "🏛 Аукцион (фиксированная цена)\n\n"
        for i, lot in enumerate(lots, start=1 + page*10):
            if lot['item_type'] == 'item':
                stats = f"+{lot['attack']} атк, +{lot['defense']} защ, +{lot['hp']} HP, +{lot['mana']} MP"
            else:
                stats = f"Восстанавливает {lot['restore_percent']}% {lot['restore_type']}"
            seller = "Гильдия" if lot['seller_type'] == 'guild' else "Игрок"
            text += f"{i}. (ID:{lot['id']}) {lot['icon']} {lot['name']} x{lot['quantity']} ({stats}) цена: {lot['price']}💰 (продавец: {seller})\n"
        keyboard = VkKeyboard()
        keyboard.add_button('🛒 Купить по ID', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'auction_buy_prompt'})
        keyboard.add_line()
        keyboard.add_button('🔄 Обновить', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'auction_refresh'})
        keyboard.add_button('📤 Выставить', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'auction_sell'})
        keyboard.add_line()
        keyboard.add_button('🏪 На рынок', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_market'})
        await send_message(vk, user_id, text, keyboard)
        user_data = await get_user_async(user_id)
        context = user_data['context']
        context['parent_state'] = 'market'
        context['auction_page'] = page
        await update_user_async(user_id, state='auction', context=context)
    except Exception as e:
        print(f"❌ Ошибка в show_auction: {e}")
        import traceback
        traceback.print_exc()
        await send_message(vk, user_id, f'⚠️ Ошибка аукциона: {e}', get_back_keyboard('рынок'))

async def show_auction_sell_menu(vk, user_id):
    """Меню продажи на аукционе"""
    try:
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        from guild import get_guild_by_character
        keyboard = VkKeyboard()
        keyboard.add_button('🗡️ Предметы (экипировка)', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'auction_sell_items'})
        keyboard.add_button('🧪 Расходники', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'auction_sell_consumables'})
        guild = await asyncio.to_thread(get_guild_by_character, char['id'])
        if guild:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute('SELECT rank FROM guild_members WHERE guild_id = ? AND character_id = ?', (guild['id'], char['id']))
            rank = cur.fetchone()
            conn.close()
            if rank and rank[0] in ('Лидер', 'Заместитель'):
                keyboard.add_line()
                keyboard.add_button('🏰 Из склада гильдии', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'auction_sell_guild'})
        keyboard.add_line()
        keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'auction_sell'})
        await send_message(vk, user_id, '📤 Что хотите выставить на аукцион?', keyboard)
        user_data = await get_user_async(user_id)
        context = user_data['context']
        context['parent_state'] = 'auction'
        await update_user_async(user_id, state='auction_sell', context=context)
    except Exception as e:
        print(f"❌ Ошибка в show_auction_sell_menu: {e}")
        await send_message(vk, user_id, f'⚠️ Ошибка: {e}', get_back_keyboard('аукцион'))

async def show_auction_sell_select_items(vk, user_id, item_type='item'):
    """Выбор предмета для продажи"""
    try:
        char = await get_character_async(user_id)
        if not char:
            return
        if item_type == 'item':
            items = get_player_items(char['id'])
            if not items:
                await send_message(vk, user_id, 'У вас нет предметов для продажи.', get_back_keyboard('аукцион'))
                return
            keyboard = VkKeyboard()
            for item in items:
                label = f"{item['icon']} {item['name']} (x{item['quantity']})"
                keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                                    payload={'cmd': 'auction_sell_select_item', 'item_id': item['id'], 'item_type': 'item'})
                keyboard.add_line()
            keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'auction_sell'})
            await send_message(vk, user_id, 'Выберите предмет для продажи:', keyboard)
        else:
            consumables = get_player_consumables(char['id'])
            if not consumables:
                await send_message(vk, user_id, 'У вас нет расходников для продажи.', get_back_keyboard('аукцион'))
                return
            keyboard = VkKeyboard()
            for c in consumables:
                label = f"{c['icon']} {c['name']} (x{c['quantity']})"
                keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                                    payload={'cmd': 'auction_sell_select_item', 'item_id': c['id'], 'item_type': 'consumable'})
                keyboard.add_line()
            keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'auction_sell'})
            await send_message(vk, user_id, 'Выберите расходник для продажи:', keyboard)
        user_data = await get_user_async(user_id)
        context = user_data['context']
        context['parent_state'] = 'auction_sell'
        await update_user_async(user_id, state='auction_sell_select', context=context)
    except Exception as e:
        print(f"❌ Ошибка в show_auction_sell_select_items: {e}")
        await send_message(vk, user_id, f'⚠️ Ошибка: {e}', get_back_keyboard('аукцион'))

async def show_auction_sell_price(vk, user_id, item_type, item_id):
    """Ввод цены для продажи"""
    try:
        user_data = await get_user_async(user_id)
        context = user_data['context']
        context['auction_item_type'] = item_type
        context['auction_item_id'] = item_id
        await update_user_async(user_id, state='awaiting_auction_price', context=context)
        await send_message(vk, user_id, 'Введите цену в серебре (целое число):')
    except Exception as e:
        print(f"❌ Ошибка в show_auction_sell_price: {e}")
        await send_message(vk, user_id, f'⚠️ Ошибка: {e}', get_back_keyboard('аукцион'))

async def show_auction_buy_confirm(vk, user_id, lot_id):
    """Подтверждение покупки лота"""
    try:
        lot = await asyncio.to_thread(get_lot_by_id, lot_id)
        if not lot:
            await send_message(vk, user_id, '❌ Лот не найден или уже неактивен.', get_back_keyboard('аукцион'))
            return
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        if char['silver'] < lot['price']:
            await send_message(vk, user_id, f'❌ Недостаточно серебра! Нужно {lot["price"]}💰.', get_back_keyboard('аукцион'))
            return
        user_data = await get_user_async(user_id)
        context = user_data['context']
        context['auction_buy_lot_id'] = lot_id
        await update_user_async(user_id, context=context)
        keyboard = VkKeyboard()
        keyboard.add_button('✅ Да, купить', color=VkKeyboardColor.POSITIVE, payload={'cmd': 'auction_confirm_yes'})
        keyboard.add_button('❌ Нет, отмена', color=VkKeyboardColor.NEGATIVE, payload={'cmd': 'auction_confirm_no'})
        keyboard.add_line()
        keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'auction'})
        await send_message(vk, user_id, f"🛒 Подтвердите покупку:\n\nЛот ID: {lot_id}\nЦена: {lot['price']}💰\nВаши деньги: {char['silver']}💰\n\nВы уверены?", keyboard)
    except Exception as e:
        print(f"❌ Ошибка в show_auction_buy_confirm: {e}")
        await send_message(vk, user_id, f'⚠️ Ошибка: {e}', get_back_keyboard('аукцион'))