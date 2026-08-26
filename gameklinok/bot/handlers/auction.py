# handlers/auction.py
from core import get_character_async, update_user_async, send_message
from auction import (get_active_auction_lots, expire_and_return_expired, 
                     buy_auction_lot, get_lot_by_id, create_auction_lot)
from guild import get_guild_by_character
from items import get_player_items
from core import get_player_consumables
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

async def show_auction(vk, user_id, page=0):
    """Показ аукциона"""
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
    keyboard.add_button('🔙 Назад в рынок', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'back'})
    await send_message(vk, user_id, text, keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'market'
    context['auction_page'] = page
    await update_user_async(user_id, state='auction', context=context)

def get_auction_keyboard():
    """Клавиатура аукциона"""
    keyboard = VkKeyboard()
    keyboard.add_button('🔄 Обновить', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'auction_refresh'})
    keyboard.add_button('📤 Выставить', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'auction_sell'})
    keyboard.add_line()
    keyboard.add_button('🏪 На рынок', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_market'})
    return keyboard