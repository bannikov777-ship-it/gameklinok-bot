# locations/inventory.py
from core import get_character_async, update_user_async, send_message, render_inventory, get_character, get_player_consumables, get_user_async
from items import get_equipped_items, get_player_items, equip_item, unequip_item
from keyboards import get_inventory_keyboard, get_inventory_actions_keyboard, get_inventory_equip_slot_keyboard, get_inventory_unequip_slot_keyboard, get_back_keyboard
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

async def show_inventory(vk, user_id):
    """Показ инвентаря"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_inventory_keyboard())
        return
    inv_items = get_player_items(char['id'])
    equipment = get_equipped_items(char['id'])
    consumables = get_player_consumables(char['id'])
    inv_text = render_inventory(inv_items, equipment, consumables, owner_id=char['id'])
    await send_message(vk, user_id, inv_text, get_inventory_actions_keyboard())
    user_data = await get_user_async(user_id)
    context = user_data['context']
    if user_data['state'] != 'inventory':
        context['return_to_inv'] = user_data['state']
        if user_data['state'] == 'profile' and 'return_to' in context:
            context['profile_return_to'] = context['return_to']
    if 'return_to_inv' not in context:
        context['return_to_inv'] = 'profile'
    await update_user_async(user_id, state='inventory', context=context)

async def show_inventory_equip(vk, user_id):
    """Меню экипировки"""
    await send_message(vk, user_id, 'Выберите слот для экипировки:', get_inventory_equip_slot_keyboard())
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'inventory'
    await update_user_async(user_id, state='inventory_equip', context=context)

async def show_inventory_unequip(vk, user_id):
    """Меню снятия экипировки"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    equipment = get_equipped_items(char['id'])
    if not equipment:
        await send_message(vk, user_id, '❌ У вас нет экипированных предметов.', get_inventory_actions_keyboard())
        return
    await send_message(vk, user_id, 'Выберите слот, с которого снять предмет:', get_inventory_unequip_slot_keyboard(equipment))
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'inventory'
    await update_user_async(user_id, state='inventory_unequip', context=context)

async def show_inventory_equip_select(vk, user_id, slot):
    """Выбор предмета для экипировки"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    inv_items = get_player_items(char['id'])
    available_items = [item for item in inv_items if item.get('slot') == slot]
    if not available_items:
        await send_message(vk, user_id, 'В вашей сумке нет предметов для этого слота.', get_inventory_equip_slot_keyboard())
        return
    keyboard = VkKeyboard()
    for item in available_items:
        label = f"{item['name']} (+{item['attack']} атк, +{item['defense']} защ)"
        keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'inv_equip_item', 'slot': slot, 'item_id': item['id']})
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'inventory_equip'})
    await send_message(vk, user_id, f'Выберите предмет для слота "{slot}":', keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'inventory'
    await update_user_async(user_id, state='inventory_equip_select', context=context)