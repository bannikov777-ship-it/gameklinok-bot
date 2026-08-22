# handlers/battle.py
from battle import process_battle_action, show_battle_potions

async def handle_battle_action(vk, user_id, action, payload=None):
    """Обработчик боевых действий"""
    if action == 'attack':
        await process_battle_action(vk, user_id, 'attack', payload)
    elif action == 'defend':
        await process_battle_action(vk, user_id, 'defend', payload)
    elif action == 'parry':
        await process_battle_action(vk, user_id, 'parry', payload)
    elif action == 'super':
        await process_battle_action(vk, user_id, 'super', payload)
    elif action == 'magic':
        await process_battle_action(vk, user_id, 'magic', payload)
    elif action == 'potion':
        await show_battle_potions(vk, user_id)
    elif action == 'use_potion' or action == 'battle_use_potion':
        await process_battle_action(vk, user_id, 'use_potion', payload)
    elif action == 'flee':
        await process_battle_action(vk, user_id, 'flee', payload)
    elif action == 'back':
        await process_battle_action(vk, user_id, 'back', payload)