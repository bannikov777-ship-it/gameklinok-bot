# locations/healer.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import asyncio
from core import (
    get_character_async, update_user_async, send_message, get_user_async,
    get_consumable_templates, buy_consumable, get_character, DB_NAME
)
from keyboards import get_back_keyboard
from crafting import get_craft_recipes, craft_item
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from .base import navigate_to

async def show_healer(vk, user_id):
    """Показ лекаря"""
    try:
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        keyboard = VkKeyboard()
        keyboard.add_button('💊 Купить зелья', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'healer_buy'})
        keyboard.add_button('🌿 Продать травы', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'healer_sell_herbs'})
        keyboard.add_line()
        keyboard.add_button('⚗️ Крафт', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'healer_craft'})
        keyboard.add_line()
        keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'back'})
        await send_message(vk, user_id, f'💊 Лекарь\nВаши 💰: {char["silver"]}\n\nВыберите действие:', keyboard)
        user_data = await get_user_async(user_id)
        context = user_data['context']
        context['parent_state'] = 'market'
        await update_user_async(user_id, state='healer', context=context)
    except Exception as e:
        print(f"❌ Ошибка в show_healer: {e}")
        import traceback
        traceback.print_exc()
        await send_message(vk, user_id, f'⚠️ Ошибка: {e}', get_back_keyboard('рынок'))

async def show_healer_buy(vk, user_id):
    """Показ покупки зелий"""
    try:
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        templates = get_consumable_templates()
        keyboard = VkKeyboard()
        count = 0
        for t in templates:
            if t['restore_type'] in ('hp', 'mana', 'stamina'):
                keyboard.add_button(f"{t['icon']} {t['name']} - {t['price']}💰", 
                                   color=VkKeyboardColor.PRIMARY,
                                   payload={'cmd': 'buy_consumable', 'template_id': t['id'], 'price': t['price']})
                count += 1
                if count % 5 == 0:
                    keyboard.add_line()
        keyboard.add_line()
        keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'healer'})
        await send_message(vk, user_id, '💊 Выберите зелье для покупки:', keyboard)
    except Exception as e:
        print(f"❌ Ошибка в show_healer_buy: {e}")
        await send_message(vk, user_id, f'⚠️ Ошибка: {e}', get_back_keyboard('лекаря'))

async def show_healer_craft(vk, user_id):
    """Показ крафта"""
    try:
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        recipes = get_craft_recipes()
        if not recipes:
            await send_message(vk, user_id, 'Нет доступных рецептов.', get_back_keyboard('лекаря'))
            return
        text = "⚗️ Доступные рецепты:\n\n"
        keyboard = VkKeyboard()
        hp_recipes = []
        mana_recipes = []
        stamina_recipes = []
        other_recipes = []
        for recipe in recipes:
            restore_type = recipe.get('restore_type')
            if restore_type == 'hp':
                hp_recipes.append(recipe)
            elif restore_type == 'mana':
                mana_recipes.append(recipe)
            elif restore_type == 'stamina':
                stamina_recipes.append(recipe)
            else:
                other_recipes.append(recipe)
        
        for recipe in recipes:
            icon = recipe.get('result_icon', '🧪')
            name = recipe.get('result_name', 'Зелье')
            percent = recipe.get('restore_percent', 0)
            ingredients_text = ", ".join([f"{ing.get('name', '')} x{ing.get('quantity', 1)}" for ing in recipe.get('ingredients', [])])
            text += f"{icon} {name} ({percent}%)\n  📦 {ingredients_text}\n\n"
        
        def add_recipe_buttons(recipe_list, type_icon, type_name):
            if not recipe_list:
                return
            for recipe in recipe_list:
                percent = recipe.get('restore_percent', 0)
                button_text = f"{type_icon} {percent}% {type_name}"
                keyboard.add_button(button_text, color=VkKeyboardColor.PRIMARY,
                                    payload={'cmd': 'healer_craft_do', 'recipe_id': recipe['id']})
            keyboard.add_line()
        
        add_recipe_buttons(hp_recipes, "❤️", "HP")
        add_recipe_buttons(mana_recipes, "💧", "MP")
        add_recipe_buttons(stamina_recipes, "⚡", "STA")
        add_recipe_buttons(other_recipes, "🧪", "?")
        keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'back'})
        await send_message(vk, user_id, text, keyboard)
        user_data = await get_user_async(user_id)
        context = user_data['context']
        context['parent_state'] = 'healer'
        await update_user_async(user_id, state='healer_craft', context=context)
    except Exception as e:
        print(f"❌ Ошибка в show_healer_craft: {e}")
        import traceback
        traceback.print_exc()
        await send_message(vk, user_id, f'⚠️ Ошибка: {e}', get_back_keyboard('лекаря'))

async def show_healer_sell_herbs(vk, user_id):
    """Продажа трав"""
    try:
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        from core import sell_all_herbs
        total, msg = sell_all_herbs(char['id'])
        await send_message(vk, user_id, msg, get_back_keyboard('лекаря'))
        await show_healer(vk, user_id)
    except Exception as e:
        print(f"❌ Ошибка в show_healer_sell_herbs: {e}")
        await send_message(vk, user_id, f'⚠️ Ошибка: {e}', get_back_keyboard('лекаря'))