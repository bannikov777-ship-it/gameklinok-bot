# locations/premium.py
import asyncio
from core import get_character_async, send_message, get_user_async, update_user_async
from keyboards import get_back_keyboard
from premium import get_premium_shop_items, buy_premium_item
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

PREMIUM_IMAGE = 'photo-240828623_456239033'

async def show_premium_shop(vk, user_id):
    """Показ премиум-магазина"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    items = await asyncio.to_thread(get_premium_shop_items)
    
    text = f"💎 Премиум магазин\n"
    text += f"Ваши 💎: {char.get('crystals', 0)}\n\n"
    
    if not items:
        text += "Товаров пока нет."
    else:
        for item in items:
            text += f"📌 ID: {item['id']} {item['icon']} {item['name']} 💰 {item['price']}💎\n"
            text += f"📝 {item['description']}\n\n"
    
    keyboard = VkKeyboard()
    keyboard.add_button('🛒 Купить по ID', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'premium_buy_prompt'})
    keyboard.add_button('🔄 Обновить', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'premium_refresh'})
    keyboard.add_line()
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    
    await send_message(vk, user_id, text, keyboard, attachment=PREMIUM_IMAGE)
    await update_user_async(user_id, state='premium_shop', context={'parent_state': 'city'})

async def show_premium_buy_prompt(vk, user_id):
    """Запрос ID товара для покупки"""
    await send_message(vk, user_id, '📝 Введите ID товара, который хотите купить:\n(можно посмотреть в списке выше)')
    await update_user_async(user_id, state='awaiting_premium_buy', context={'parent_state': 'premium_shop'})

async def show_premium_buy_confirm(vk, user_id, item_id):
    """Подтверждение покупки"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    items = await asyncio.to_thread(get_premium_shop_items)
    item = next((i for i in items if i['id'] == item_id), None)
    if not item:
        await send_message(vk, user_id, '❌ Товар не найден.', get_back_keyboard('премиум магазин'))
        return
    
    if char.get('crystals', 0) < item['price']:
        await send_message(vk, user_id, f'❌ Недостаточно кристаллов! Нужно {item["price"]}💎.', get_back_keyboard('премиум магазин'))
        return
    
    keyboard = VkKeyboard()
    keyboard.add_button('✅ Да, купить', color=VkKeyboardColor.POSITIVE, 
                       payload={'cmd': 'premium_buy_confirm', 'item_id': item_id})
    keyboard.add_button('❌ Отмена', color=VkKeyboardColor.NEGATIVE, 
                       payload={'cmd': 'premium_buy_cancel'})
    
    await send_message(vk, user_id, 
        f"🛒 Подтвердите покупку:\n\n"
        f"{item['icon']} {item['name']}\n"
        f"💰 Цена: {item['price']}💎\n"
        f"Ваши 💎: {char.get('crystals', 0)}\n\n"
        f"Вы уверены?", keyboard)

async def show_premium_buy_execute(vk, user_id, item_id):
    """Выполнение покупки"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    success, msg = await asyncio.to_thread(buy_premium_item, char['id'], item_id)
    
    if success:
        await send_message(vk, user_id, f'✅ {msg}', get_back_keyboard('премиум магазин'))
        await show_premium_shop(vk, user_id)
    else:
        await send_message(vk, user_id, f'❌ {msg}', get_back_keyboard('премиум магазин'))
        await show_premium_shop(vk, user_id)