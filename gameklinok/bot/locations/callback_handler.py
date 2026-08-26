# locations/callback_handler.py - ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ

import sqlite3
import asyncio
import random
import time
from config import DB_NAME
from core import (
    get_character_async, update_user_async, send_message, get_user_async,
    create_character, recalc_stats_async, get_character,
    get_equipment, get_inventory, equip_item, unequip_item,
    get_player_consumables, buy_consumable, get_player_crystals,
    add_herb, get_consumable_templates
)
from items import upgrade_item, generate_shop_item, get_item_stats, get_item_template_id_by_name
from guild import join_guild, get_guild_by_character, get_all_guilds, set_rank, kick_member, add_to_guild_storage, remove_from_guild_storage
from auction import buy_auction_lot, get_lot_by_id, create_auction_lot
from quests import take_quest
from tower import get_tower_party, create_tower_party, leave_tower, rest_in_tower, start_tower_battle
from battle import process_battle_action
from keyboards import get_back_keyboard, get_gender_keyboard, get_class_choice_keyboard
from scheduler import scheduler
from locations.tavern import restore_after_sleep
from handlers.mail import show_mail, show_mail_read, show_mail_delete, show_mail_write
from handlers.tower_handlers import handle_tower_commands
from handlers.guild_quests import handle_guild_quests
from admin import admin_codes_menu, admin_show_codes, admin_create_code
from locations.admin_panel import show_admin_panel
from locations.scrolls import show_scrolls, use_scroll
from locations.premium import show_premium_shop, show_premium_buy_prompt, show_premium_buy_confirm, show_premium_buy_execute
from locations.codes import show_codes_menu, process_code_enter

# Импортируем функции из locations
from . import (
    show_city, show_city2, show_guild, show_market, show_healer, 
    show_auction, show_smithy, show_church, show_market_shop, 
    show_hunters, show_tavern, show_town_hall, show_profile, 
    show_inventory, show_exit, show_forest, show_graveyard, 
    show_meadow, show_rating, show_guild_donate, show_guild_withdraw,
    show_guild_donate_confirm, show_guild_withdraw_confirm, 
    show_guild_members, show_guild_storage, show_guild_stats,
    show_guild_manage, show_guild_manage_by_id, show_guild_manage_member_by_id,
    show_guild_chat,
    show_hunters_quests, show_hunters_my_quests, show_hunters_take_quest,
    show_hunters_sell, show_healer_buy, show_healer_craft, 
    show_healer_sell_herbs, show_smithy_upgrade_menu, 
    show_tavern_food, show_tavern_room, show_church_remove_debuff,
    show_inventory_equip, show_inventory_unequip, show_inventory_equip_select,
    forest_deep, forest_wander,
    graveyard_deep, graveyard_wander, meadow_herbs,
    show_tower
)

# Импортируем функции из market отдельно
from locations.market import show_market_category, show_market_buy_item
from locations.tower import show_tower_chat
from locations.graveyard import back_to_exit as graveyard_back_to_exit

async def show_tower_chat(vk, user_id):
    """Показ чата группы башни"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    party = await asyncio.to_thread(get_tower_party, char['id'])
    if not party:
        await send_message(vk, user_id, 'Вы не в группе башни.', get_back_keyboard('башня'))
        await show_tower(vk, user_id)
        return
    
    from keyboards import get_tower_chat_keyboard
    keyboard = get_tower_chat_keyboard()
    
    await send_message(vk, user_id, '💬 Чат группы башни\n\nНапишите сообщение, и оно будет отправлено всем участникам группы.', keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'tower'
    await update_user_async(user_id, state='tower_chat', context=context)

async def show_sleep_status(vk, user_id):
    """Показ статуса сна"""
    user_data = await get_user_async(user_id)
    context = user_data['context']
    sleep_end_time = context.get('sleep_end_time')
    if not sleep_end_time:
        await send_message(vk, user_id, 'Вы сейчас не спите.', get_back_keyboard('таверну'))
        return
    remaining = max(0, sleep_end_time - time.time())
    hours = int(remaining // 3600)
    minutes = int((remaining % 3600) // 60)
    seconds = int(remaining % 60)
    from keyboards import get_sleep_status_keyboard
    await send_message(vk, user_id, f'⏳ До пробуждения осталось: {hours}ч {minutes}м {seconds}с', get_sleep_status_keyboard())


async def handle_callback(vk, user_id, payload):
    """Обработчик callback-кнопок"""
    print(f"📩 handle_callback: payload={payload}")

    if 'gender' in payload:
        gender = payload['gender']
        user_data = await get_user_async(user_id)
        context = user_data['context']
        name = context.get('name')
        if not name:
            await send_message(vk, user_id, 'Сначала введите имя.', get_back_keyboard('город'))
            return
        await asyncio.to_thread(create_character, user_id, name, gender)
        await send_message(vk, user_id, f'🎉 Поздравляю, {name}!\nТы выбрал пол: {"♂ Мужской" if gender == "male" else "♀ Женский"}.\nТеперь ты в Стальном Троне.\n\nДостигни 20 уровня, чтобы выбрать класс в Ратуше.', get_back_keyboard('город'))
        await show_city(vk, user_id)
        return

    if 'class' in payload:
        class_name = payload['class']
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        if char['level'] < 20:
            await send_message(vk, user_id, f'❌ Выбор класс доступен только с 20 уровня. Ваш уровень: {char["level"]}.', get_back_keyboard('ратушу'))
            return
        if char['class']:
            await send_message(vk, user_id, f'Вы уже выбрали класс: {char["class"]}.', get_back_keyboard('ратушу'))
            return
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('UPDATE characters SET class = ? WHERE id = ?', (class_name, char['id']))
        conn.commit()
        conn.close()
        await recalc_stats_async(char['id'])
        await send_message(vk, user_id, f'✅ Вы выбрали класс: {class_name}! Статы обновлены.', get_back_keyboard('ратушу'))
        await show_town_hall(vk, user_id)
        return

    cmd = payload.get('cmd')
    if cmd is None:
        await show_city(vk, user_id)
        return

    # ---- БАШНЯ ----
    if await handle_tower_commands(vk, user_id, cmd, payload):
        return

    # ---- ГИЛЬДЕЙСКИЕ КВЕСТЫ ----
    if await handle_guild_quests(vk, user_id, cmd, payload):
        return

    # ---- БОЙ ----
    if cmd.startswith('battle_'):
        action = cmd[7:]
        await process_battle_action(vk, user_id, action, payload)
        return

 # ---- НАВИГАЦИЯ (явные переходы) ----
    if cmd == 'go_city':
        from .base import navigate_to
        await navigate_to(vk, user_id, 'city')
        return
    
    if cmd == 'go_meadow':
        from .base import navigate_to
        await navigate_to(vk, user_id, 'meadow')
        return

    if cmd == 'go_город':
        from .base import navigate_to
        await navigate_to(vk, user_id, 'meadow')
        return

    if cmd == 'go_инвентарь':
        await show_inventory(vk, user_id)
        return

    if cmd == 'go_market':
        from .base import navigate_to
        await navigate_to(vk, user_id, 'market')
        return

    if cmd == 'go_tavern':
        from .base import navigate_to
        await navigate_to(vk, user_id, 'tavern')
        return

    if cmd == 'go_healer':
        from .base import navigate_to
        await navigate_to(vk, user_id, 'healer')
        return

    if cmd == 'go_profile':
        await show_profile(vk, user_id)
        return

    if cmd == 'go_inventory':
        await show_inventory(vk, user_id)
        return

    if cmd == 'go_exit':
        from .base import navigate_to
        await navigate_to(vk, user_id, 'exit')
        return

    if cmd == 'go_forest':
        from .base import navigate_to
        await navigate_to(vk, user_id, 'forest')
        return

    if cmd == 'go_graveyard':
        from .base import navigate_to
        await navigate_to(vk, user_id, 'graveyard')
        return

    if cmd == 'go_tower':
        from .base import navigate_to
        await navigate_to(vk, user_id, 'tower')
        return

    if cmd == 'go_guild':
        from .base import navigate_to
        await navigate_to(vk, user_id, 'guild')
        return

    if cmd == 'go_church':
        from .base import navigate_to
        await navigate_to(vk, user_id, 'church')
        return

    # ---- ПРОМОКОДЫ ----
    if cmd == 'code_menu':
        await show_codes_menu(vk, user_id)
        return

    if cmd == 'code_enter':
        await send_message(vk, user_id, '📝 Введите промокод:')
        await update_user_async(user_id, state='awaiting_code', context={'parent_state': 'city'})
        return

    if cmd == 'copy_code':
        code = payload.get('code')
        if code:
            await send_message(vk, user_id, f'📋 Код скопирован:\n`{code}`')
        return

    # ---- СВИТКИ ----
    if cmd == 'scrolls':
        await show_scrolls(vk, user_id)
        return

    if cmd == 'scroll_use':
        scroll_id = payload.get('scroll_id')
        scroll_type = payload.get('type', 'curse_remove')
        if scroll_id:
            await use_scroll(vk, user_id, scroll_id, scroll_type)
        else:
            await send_message(vk, user_id, '❌ Ошибка: свиток не найден.', get_back_keyboard('инвентарь'))
        return

    # ---- ПРЕМИУМ МАГАЗИН ----
    if cmd == 'premium_shop':
        await show_premium_shop(vk, user_id)
        return

    if cmd == 'premium_buy_prompt':
        await show_premium_buy_prompt(vk, user_id)
        return

    if cmd == 'premium_buy_confirm':
        item_id = payload.get('item_id')
        if item_id:
            await show_premium_buy_execute(vk, user_id, item_id)
        return

    if cmd == 'premium_buy_cancel':
        await send_message(vk, user_id, '❌ Покупка отменена.', get_back_keyboard('премиум магазин'))
        await show_premium_shop(vk, user_id)
        return

    if cmd == 'premium_refresh':
        await show_premium_shop(vk, user_id)
        return

    # ---- АДМИН-ПАНЕЛЬ ----
    if cmd == 'admin_panel':
        await show_admin_panel(vk, user_id)
        return

    if cmd == 'admin_codes_menu':
        await admin_codes_menu(vk, user_id)
        return

    if cmd == 'admin_codes_list':
        await admin_show_codes(vk, user_id)
        return

    if cmd == 'admin_code_create':
        amount = payload.get('amount', 100)
        reward_type = payload.get('type', 'crystals')
        await admin_create_code(vk, user_id, amount=amount, reward_type=reward_type)
        return

    if cmd == 'admin_codes_refresh':
        await admin_show_codes(vk, user_id)
        return

    # ---- ЧАТ БАШНИ ----
    if cmd == 'tower_chat_show':
        await show_tower_chat(vk, user_id)
        return

    if cmd == 'tower_chat_send':
        await update_user_async(user_id, state='awaiting_tower_message', context={'parent_state': 'tower_chat'})
        await send_message(vk, user_id, 'Введите сообщение для чата группы башни:')
        return

    # ---- ИНВЕНТАРЬ ----
    if cmd == 'inventory':
        await show_inventory(vk, user_id)
        return

    if cmd == 'inventory_equip':
        await show_inventory_equip(vk, user_id)
        return

    if cmd == 'inventory_unequip':
        await show_inventory_unequip(vk, user_id)
        return

    if cmd == 'inventory_equip_prompt':
        await send_message(vk, user_id, '📝 Введите ID предмета, который хотите экипировать:')
        await update_user_async(user_id, state='awaiting_inventory_equip_id', context={'parent_state': 'inventory'})
        return

    if cmd == 'inventory_unequip_prompt':
        await send_message(vk, user_id, '📝 Введите ID предмета, который хотите снять:')
        await update_user_async(user_id, state='awaiting_inventory_unequip_id', context={'parent_state': 'inventory'})
        return

    if cmd == 'inv_equip_slot':
        slot = payload.get('slot')
        await show_inventory_equip_select(vk, user_id, slot)
        return

    if cmd == 'inv_equip_item':
        slot = payload.get('slot')
        item_id = payload.get('item_id')
        char = await get_character_async(user_id)
        if char:
            equip_item(char['id'], item_id, slot)
            await recalc_stats_async(char['id'])
            await send_message(vk, user_id, '✅ Предмет надет!', get_back_keyboard('инвентарь'))
            await show_inventory(vk, user_id)
        return

    if cmd == 'inv_unequip_slot':
        slot = payload.get('slot')
        char = await get_character_async(user_id)
        if char:
            unequip_item(char['id'], slot)
            await recalc_stats_async(char['id'])
            await send_message(vk, user_id, '✅ Предмет снят в инвентарь.', get_back_keyboard('инвентарь'))
            await show_inventory(vk, user_id)
        return

    # ---- МАГАЗИН ----
    if cmd == 'market_shop':
        await show_market_shop(vk, user_id)
        return

    if cmd == 'market_category':
        category = payload.get('category')
        await show_market_category(vk, user_id, category)
        return

    if cmd == 'market_buy_item':
        template_name = payload.get('template')
        price = payload.get('price')
        shop_level = payload.get('shop_level', 1)
        rarity = payload.get('rarity', 1)
        await show_market_buy_item(vk, user_id, template_name, price, shop_level, rarity)
        return

    if cmd == 'market_buy_confirm':
        template_name = payload.get('template')
        price = payload.get('price')
        shop_level = payload.get('shop_level', 1)
        rarity = payload.get('rarity', 1)
    
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
    
        if char['silver'] < price:
            await send_message(vk, user_id, f'❌ Недостаточно серебра! Нужно {price}💰.', get_back_keyboard('магазин'))
            return
    
        item_id = generate_shop_item(char['id'], template_name, shop_level)
        if not item_id:
            await send_message(vk, user_id, '❌ Ошибка при создании предмета.', get_back_keyboard('магазин'))
            return
    
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('UPDATE characters SET silver = silver - ? WHERE id = ?', (price, char['id']))
        conn.commit()
        conn.close()
    
        from core import get_item_prefix
        await send_message(vk, user_id, f'✅ Вы купили **{get_item_prefix(shop_level)} {template_name}** за {price}💰!', get_back_keyboard('магазин'))
        await show_market_shop(vk, user_id)
        return

    # ---- ЛЕКАРЬ ----
    if cmd == 'market_healer':
        await show_healer(vk, user_id)
        return

    if cmd == 'healer_buy':
        await show_healer_buy(vk, user_id)
        return

    if cmd == 'healer_craft':
        await show_healer_craft(vk, user_id)
        return

    if cmd == 'healer_craft_do':
        recipe_id = payload.get('recipe_id')
        if not recipe_id:
            await send_message(vk, user_id, 'Ошибка: рецепт не указан.', get_back_keyboard('лекаря'))
            return
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        from crafting import craft_item
        try:
            success, msg = await asyncio.to_thread(craft_item, char['id'], recipe_id)
            await send_message(vk, user_id, f'{"✅" if success else "❌"} {msg}')
            await show_healer_craft(vk, user_id)
        except Exception as e:
            await send_message(vk, user_id, f'❌ Ошибка при крафте: {e}')
            import traceback
            traceback.print_exc()
            await show_healer_craft(vk, user_id)
        return

    if cmd == 'buy_consumable':
        template_id = payload.get('template_id')
        price = payload.get('price')
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        success, msg = buy_consumable(char['id'], template_id, 1)
        if success:
            await send_message(vk, user_id, f'✅ {msg}')
            await show_healer_buy(vk, user_id)
        else:
            await send_message(vk, user_id, f'❌ {msg}')
            await show_healer_buy(vk, user_id)
        return

    if cmd == 'healer_sell_herbs':
        await show_healer_sell_herbs(vk, user_id)
        return

    # ---- КУЗНИЦА ----
    if cmd == 'smithy':
        await show_smithy(vk, user_id)
        return

    if cmd == 'smithy_select_item':
        item_id = payload.get('item_id')
        if not item_id:
            await send_message(vk, user_id, 'Ошибка: не выбран предмет.', get_back_keyboard('кузница'))
            return
        await show_smithy_upgrade_menu(vk, user_id, item_id)
        return

    if cmd == 'smithy_upgrade':
        crystal_id = payload.get('crystal_id')
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        user_data = await get_user_async(user_id)
        context = user_data['context']
        item_id = context.get('smithy_item_id')
        if not item_id:
            await send_message(vk, user_id, 'Ошибка: предмет не выбран.', get_back_keyboard('кузница'))
            return
        success, msg = upgrade_item(item_id, crystal_id)
        if success:
            await send_message(vk, user_id, f'✅ {msg}', get_back_keyboard('кузница'))
        else:
            await send_message(vk, user_id, f'❌ {msg}', get_back_keyboard('кузница'))
        await show_smithy(vk, user_id)
        return

    # ---- СОБОР ----
    if cmd == 'church':
        await show_church(vk, user_id)
        return

    if cmd == 'church_remove_debuff':
        await show_church_remove_debuff(vk, user_id, 1)
        return

    if cmd == 'church_remove_tower_debuff':
        await show_church_remove_debuff(vk, user_id, 2)
        return

    # ---- РЕЙТИНГ ----
    if cmd == 'rating':
        await show_rating(vk, user_id)
        return

    # ---- ГИЛЬДИИ ----
    if cmd == 'guild':
        await show_guild(vk, user_id)
        return

    if cmd == 'guild_donate':
        await show_guild_donate(vk, user_id)
        return

    if cmd == 'guild_withdraw':
        await show_guild_withdraw(vk, user_id)
        return

    if cmd == 'guild_manage_by_id':
        from locations.guild import show_guild_manage_by_id
        await show_guild_manage_by_id(vk, user_id)
        return

    if cmd == 'go_гильдию':
        await show_guild(vk, user_id)
        return

    if cmd == 'guild_applications':
        from locations.guild import show_guild_applications
        await show_guild_applications(vk, user_id)
        return

    if cmd == 'guild_members':
        from locations.guild import show_guild_members
        await show_guild_members(vk, user_id)
        return

    if cmd == 'guild_storage':
        from locations.guild import show_guild_storage
        await show_guild_storage(vk, user_id)
        return

    if cmd == 'guild_storage_add':
        from locations.guild import show_guild_storage_add
        await show_guild_storage_add(vk, user_id)
        return

    if cmd == 'guild_storage_add_items':
        from locations.guild import show_guild_storage_add_items
        await show_guild_storage_add_items(vk, user_id)
        return

    if cmd == 'guild_storage_add_crystals':
        from locations.guild import show_guild_storage_add_crystals
        await show_guild_storage_add_crystals(vk, user_id)
        return

    if cmd == 'guild_storage_add_item_confirm':
        item_id = payload.get('item_id')
        item_type = payload.get('type', 'item')
        if item_id:
            from locations.guild import show_guild_storage_add_item_confirm
            await show_guild_storage_add_item_confirm(vk, user_id, item_id, item_type)
        return

    if cmd == 'guild_storage_remove_prompt':
        from locations.guild import show_guild_storage_remove_prompt
        await show_guild_storage_remove_prompt(vk, user_id)
        return

    if cmd == 'guild_storage_remove':
        storage_id = payload.get('storage_id')
        quantity = payload.get('quantity', 1)
        if storage_id:
            from locations.guild import show_guild_storage_remove_confirm
            await show_guild_storage_remove_confirm(vk, user_id, storage_id, quantity)
        return

    if cmd == 'guild_stats':
        from locations.guild import show_guild_stats
        await show_guild_stats(vk, user_id)
        return

    if cmd == 'guild_manage':
        from locations.guild import show_guild_manage
        await show_guild_manage(vk, user_id)
        return

    # ✅ ИСПРАВЛЕНО: назначение ранга - возврат в управление
    if cmd == 'guild_set_rank':
        member_id = payload.get('member_id')
        new_rank = payload.get('rank')
        if member_id and new_rank:
            char = await get_character_async(user_id)
            if not char:
                await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
                return
            success, msg = set_rank(char['id'], member_id, new_rank)
            if success:
                await send_message(vk, user_id, f'✅ {msg}')
            else:
                await send_message(vk, user_id, f'❌ {msg}')
            # ✅ Возвращаем в управление гильдией
            from locations.guild import show_guild_manage
            await show_guild_manage(vk, user_id)
        return

    # ✅ ИСПРАВЛЕНО: исключение участника - возврат в управление
    if cmd == 'guild_kick':
        member_id = payload.get('member_id')
        if member_id:
            char = await get_character_async(user_id)
            if not char:
                await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
                return
            success, msg = kick_member(char['id'], member_id)
            if success:
                await send_message(vk, user_id, f'✅ {msg}')
            else:
                await send_message(vk, user_id, f'❌ {msg}')
            # ✅ Возвращаем в управление гильдией
            from locations.guild import show_guild_manage
            await show_guild_manage(vk, user_id)
        return

    if cmd == 'guild_chat':
        from locations.guild import show_guild_chat
        await show_guild_chat(vk, user_id)
        return

    if cmd == 'guild_chat_send':
        await update_user_async(user_id, state='awaiting_guild_message', context={'parent_state': 'guild_chat'})
        await send_message(vk, user_id, 'Введите сообщение для чата гильдии:')
        return

    # ---- ТАВЕРНА ----
    if cmd == 'tavern':
        await show_tavern(vk, user_id)
        return
    
    if cmd == 'tavern_food':
        await show_tavern_food(vk, user_id)
        return
    
    if cmd == 'tavern_room':
        await show_tavern_room(vk, user_id)
        return
    
    if cmd == 'tavern_quests':
        await send_message(vk, user_id, '📜 Доступные квесты:\n1. Принести шкуры волков\n2. Найти пропавший амулет\n(пока заглушка)', get_back_keyboard('таверну'))
        user_data = await get_user_async(user_id)
        context = user_data['context']
        context['parent_state'] = 'tavern'
        await update_user_async(user_id, state='tavern_quests', context=context)
        return
    
    if cmd == 'tavern_rumors':
        await send_message(vk, user_id, '🗣 Слухи: говорят, в Пустошах видели светящийся камень. И ещё — в Стальном Троне кто-то ищет отважных искателей.', get_back_keyboard('таверну'))
        user_data = await get_user_async(user_id)
        context = user_data['context']
        context['parent_state'] = 'tavern'
        await update_user_async(user_id, state='tavern_rumors', context=context)
        return

    # ---- ЕДА ----
    if cmd == 'buy_food':
        percent = payload.get('percent')
        price = payload.get('price')
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        if char['silver'] < price:
            await send_message(vk, user_id, f'❌ Недостаточно серебра! Нужно {price}💰.', get_back_keyboard('таверну'))
            return
        max_hp = char['max_hp']
        restore = int(max_hp * percent / 100)
        new_hp = min(max_hp, char['hp'] + restore)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('UPDATE characters SET silver = silver - ?, hp = ? WHERE id = ?', (price, new_hp, char['id']))
        conn.commit()
        conn.close()
        await send_message(vk, user_id, f'✅ Вы съели еду и восстановили {restore} HP (теперь {new_hp}/{max_hp}).', get_back_keyboard('таверну'))
        await show_tavern(vk, user_id)
        return

    # ---- СОН ----
    if cmd == 'sleep':
        percent = payload.get('percent')
        hours = payload.get('hours', 1)
        price = payload.get('price', 0)
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        
        if char['silver'] < price:
            await send_message(vk, user_id, f'❌ Недостаточно серебра! Нужно {price}💰.', get_back_keyboard('таверну'))
            return
        
        user_data = await get_user_async(user_id)
        context = user_data['context']
        if 'sleep_task_id' in context:
            scheduler.cancel(context['sleep_task_id'])
        
        from keyboards import get_sleep_status_keyboard
        
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('UPDATE characters SET silver = silver - ? WHERE id = ?', (price, char['id']))
        conn.commit()
        conn.close()
        
        await send_message(vk, user_id,
            f'😴 Вы легли спать на {hours} час(а). Восстановится {percent}% HP, {percent}% MP и {percent}% Stamina.\n'
            f'💰 Снято {price} серебра\n\n'
            f'Вы можете выйти из комнаты, чтобы отменить сон.',
            get_sleep_status_keyboard()
        )
        task_id = scheduler.schedule(hours * 3600, restore_after_sleep, vk, user_id, percent)
        context['sleep_task_id'] = task_id
        context['sleep_end_time'] = time.time() + hours * 3600
        await update_user_async(user_id, state='tavern_room', context=context)
        return

    if cmd == 'sleep_check':
        await show_sleep_status(vk, user_id)
        return

    if cmd == 'sleep_cancel':
        user_data = await get_user_async(user_id)
        context = user_data['context']
        if 'sleep_task_id' in context:
            scheduler.cancel(context['sleep_task_id'])
            del context['sleep_task_id']
            del context['sleep_end_time']
            await update_user_async(user_id, context=context)
            await send_message(vk, user_id, '❌ Вы проснулись! Восстановление отменено.', get_back_keyboard('таверну'))
        else:
            await send_message(vk, user_id, 'Вы и так не спите.', get_back_keyboard('таверну'))
        await show_tavern(vk, user_id)
        return

    # ---- АУКЦИОН ----
    if cmd == 'market_auction':
        await show_auction(vk, user_id)
        return

    if cmd == 'auction_refresh':
        user_data = await get_user_async(user_id)
        page = user_data['context'].get('auction_page', 0)
        await show_auction(vk, user_id, page)
        return

    if cmd == 'auction_buy_prompt':
        await send_message(vk, user_id, 'Введите ID лота, который хотите купить (только число):')
        await update_user_async(user_id, state='awaiting_auction_buy_id', context={'parent_state': 'auction'})
        return

    if cmd == 'auction_sell':
        from .auction import show_auction_sell_menu
        await show_auction_sell_menu(vk, user_id)
        return

    if cmd == 'auction_sell_items':
        from .auction import show_auction_sell_select_items
        await show_auction_sell_select_items(vk, user_id, 'item')
        return

    if cmd == 'auction_sell_consumables':
        from .auction import show_auction_sell_select_items
        await show_auction_sell_select_items(vk, user_id, 'consumable')
        return

    if cmd == 'auction_sell_select_item':
        item_type = payload.get('item_type')
        item_id = payload.get('item_id')
        from .auction import show_auction_sell_price
        await show_auction_sell_price(vk, user_id, item_type, item_id)
        return

    if cmd == 'auction_sell_guild':
        await send_message(vk, user_id, '🏰 Продажа из склада гильдии пока в разработке.', get_back_keyboard('аукцион'))
        return

    if cmd == 'auction_confirm_yes':
        user_data = await get_user_async(user_id)
        context = user_data['context']
        lot_id = context.get('auction_buy_lot_id')
        if not lot_id:
            await send_message(vk, user_id, 'Ошибка: лот не найден.', get_back_keyboard('аукцион'))
            return
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        success, msg = buy_auction_lot(lot_id, char['id'])
        if success:
            await send_message(vk, user_id, msg, get_back_keyboard('аукцион'))
        else:
            await send_message(vk, user_id, f'❌ {msg}', get_back_keyboard('аукцион'))
        context.pop('auction_buy_lot_id', None)
        await update_user_async(user_id, state='auction', context=context)
        await show_auction(vk, user_id)
        return

    if cmd == 'auction_confirm_no':
        user_data = await get_user_async(user_id)
        context = user_data['context']
        context.pop('auction_buy_lot_id', None)
        await update_user_async(user_id, state='auction', context=context)
        await send_message(vk, user_id, '❌ Покупка отменена.', get_back_keyboard('аукцион'))
        await show_auction(vk, user_id)
        return

    # ---- ГИЛЬДИЯ ОХОТНИКОВ ----
    if cmd == 'hunters':
        await show_hunters(vk, user_id)
        return

    if cmd == 'hunters_sell':
        await show_hunters_sell(vk, user_id)
        return

    if cmd == 'hunters_quests':
        await show_hunters_quests(vk, user_id)
        return

    if cmd == 'hunters_my_quests':
        await show_hunters_my_quests(vk, user_id)
        return

    if cmd == 'hunters_take_quest':
        quest_id = payload.get('quest_id')
        if quest_id:
            await show_hunters_take_quest(vk, user_id, quest_id)
        else:
            await send_message(vk, user_id, 'Ошибка: не указан квест.', get_back_keyboard('гильдию охотников'))
        return

    # ---- ПОЧТА ----
    if cmd == 'mail':
        await show_mail(vk, user_id)
        return

    if cmd == 'mail_read':
        mail_id = payload.get('mail_id')
        if mail_id:
            await show_mail_read(vk, user_id, mail_id)
        else:
            await send_message(vk, user_id, 'Ошибка: письмо не указано.', get_back_keyboard('почту'))
        return

    if cmd == 'mail_delete':
        mail_id = payload.get('mail_id')
        if mail_id:
            await show_mail_delete(vk, user_id, mail_id)
        else:
            await send_message(vk, user_id, 'Ошибка: письмо не указано.', get_back_keyboard('почту'))
        return

    if cmd == 'mail_write':
        await show_mail_write(vk, user_id)
        return

    if cmd == 'mail_claim_attachment':
        mail_id = payload.get('mail_id')
        if mail_id:
            from handlers.mail import show_mail_claim_attachment
            await show_mail_claim_attachment(vk, user_id, mail_id)
        else:
            await send_message(vk, user_id, 'Ошибка: письмо не указано.', get_back_keyboard('почту'))
        return

    if cmd == 'mail_attachment_menu':
        from handlers.mail import show_mail_attachment_menu
        await show_mail_attachment_menu(vk, user_id)
        return

    if cmd == 'mail_attach_money':
        from handlers.mail import show_mail_attach_money
        await show_mail_attach_money(vk, user_id)
        return

    if cmd == 'mail_attach_item':
        from handlers.mail import show_mail_attach_item
        await show_mail_attach_item(vk, user_id)
        return

    if cmd == 'mail_attach_consumable':
        from handlers.mail import show_mail_attach_consumable
        await show_mail_attach_consumable(vk, user_id)
        return

    if cmd == 'mail_attach_item_select':
        item_id = payload.get('item_id')
        if item_id:
            from handlers.mail import show_mail_attach_quantity
            await show_mail_attach_quantity(vk, user_id, item_id, 'item')
        else:
            await send_message(vk, user_id, 'Ошибка: предмет не указан.', get_back_keyboard('почту'))
        return

    if cmd == 'mail_attach_consumable_select':
        item_id = payload.get('item_id')
        if item_id:
            from handlers.mail import show_mail_attach_quantity
            await show_mail_attach_quantity(vk, user_id, item_id, 'consumable')
        else:
            await send_message(vk, user_id, 'Ошибка: расходник не указан.', get_back_keyboard('почту'))
        return

    if cmd == 'mail_attach_none':
        from handlers.mail import show_mail_attach_none
        await show_mail_attach_none(vk, user_id)
        return

    # ---- ЛЕС ПОСЛЕ БОЯ ----
    if cmd == 'forest_deep':
        await forest_deep(vk, user_id)
        return

    if cmd == 'forest_wander':
        await forest_wander(vk, user_id)
        return

    if cmd == 'back_to_exit':
        await graveyard_back_to_exit(vk, user_id)
        return

    # ---- КЛАДБИЩЕ ----
    if cmd == 'graveyard':
        from locations.graveyard import show_graveyard
        await show_graveyard(vk, user_id)
        return

    if cmd == 'graveyard_deep':
        from locations.graveyard import graveyard_deep
        await graveyard_deep(vk, user_id)
        return

    if cmd == 'graveyard_wander':
        from locations.graveyard import graveyard_wander
        await graveyard_wander(vk, user_id)
        return
    
    # ---- ОСТАЛЬНЫЕ КОМАНДЫ ----
    if cmd == 'back_to_city':
        await show_city(vk, user_id)
        return

    if cmd == 'profile':
        await show_profile(vk, user_id)
        return

    if cmd == 'exit_city':
        await show_exit(vk, user_id)
        return

    if cmd == 'exit_city2':
        await show_meadow(vk, user_id)
        return

    if cmd == 'forest':
        await show_forest(vk, user_id)
        return

    if cmd == 'meadow':
        await show_meadow(vk, user_id)
        return

    if cmd == 'meadow_tower':
        await show_tower(vk, user_id)
        return

    if cmd == 'meadow_city':
        await show_city2(vk, user_id)
        return

    if cmd == 'meadow_herbs':
        await meadow_herbs(vk, user_id)
        return

    if cmd == 'town_hall':
        await show_town_hall(vk, user_id)
        return

    if cmd == 'town_hall_class':
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        if char['level'] < 20:
            await send_message(vk, user_id, '❌ Выбор класс доступен только с 20 уровня.', get_back_keyboard('ратушу'))
            return
        if char['class']:
            await send_message(vk, user_id, f'Вы уже выбрали класс: {char["class"]}.', get_back_keyboard('ратушу'))
            return
        await send_message(vk, user_id, 'Выберите свой класс:', get_class_choice_keyboard())
        return

    if cmd == 'market':
        await show_market(vk, user_id)
        return

    if cmd == 'create_character':
        if await get_character_async(user_id):
            await send_message(vk, user_id, 'У вас уже есть персонаж!', get_back_keyboard('город'))
            return
        await send_message(vk, user_id, 'Как назовёшь своего героя? Напиши имя в ответ.')
        await update_user_async(user_id, state='awaiting_name', context={'step': 'name'})
        return

    # Если ничего не подошло - показываем город
    await show_city(vk, user_id)