# main.py - исправленный для хостинга
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
import json
import traceback
import sqlite3
from vkbottle.bot import Bot, Message

from config import TOKEN, DB_NAME
from core import (init_db, get_character_async, update_user_async, get_user_async, 
                  send_message, create_character, recalc_stats_async, get_character)
from core.database import seed_cities, seed_consumables, seed_herbs, seed_guild_quests, seed_premium_shop
from items import init_items_db, seed_item_templates
from resources import seed_resources
from crafting import seed_craft_recipes
from quests import seed_hunter_quests
from tower import seed_tower_bosses, get_tower_party, send_tower_chat_message, invite_to_tower_party
from guild import create_guild, get_guild_by_character, send_guild_message, get_guild_members
from scheduler import scheduler
from locations import (handle_callback, show_city, show_guild, show_tower,
                       show_market, show_healer, show_auction, show_smithy,
                       show_church, show_market_shop, show_hunters, show_tavern,
                       show_town_hall, show_profile, show_inventory, show_exit,
                       show_forest, show_graveyard, show_meadow, show_rating,
                       show_guild_donate, show_guild_withdraw, show_guild_donate_confirm,
                       show_guild_withdraw_confirm, show_guild_members, show_guild_storage,
                       show_guild_stats, show_guild_manage, show_guild_manage_by_id, show_guild_manage_member_by_id,
                       show_guild_chat, show_hunters_quests, show_hunters_my_quests,
                       show_hunters_take_quest, show_hunters_sell, show_hunters,
                       show_healer_buy, show_healer_craft, show_healer_sell_herbs,
                       show_smithy_upgrade_menu, show_tavern_food, show_tavern_room,
                       show_church_remove_debuff, show_inventory_equip, show_inventory_unequip,
                       show_inventory_equip_select, show_tower_chat, show_auction_buy_confirm,
                       show_premium_shop, show_premium_buy_confirm, show_premium_buy_execute,
                       show_premium_buy_prompt)
from handlers import (handle_battle_action, show_mail, show_mail_read, show_mail_delete, 
                      show_mail_write, show_mail_write_subject, show_mail_write_body,
                      show_mail_send, show_mail_attachment_menu, show_mail_attach_money,
                      show_mail_attach_item, show_mail_attach_quantity,
                      show_mail_attach_none, show_mail_claim_attachment, show_mail_send_with_attachment)
from keyboards import (get_gender_keyboard, get_back_keyboard, get_lore_keyboard, 
                       get_tower_chat_keyboard, get_guild_chat_keyboard, get_mail_keyboard,
                       get_mail_attachment_keyboard)
from guild_quests import refresh_guild_quests
from admin import admin_codes_menu, admin_create_code, admin_show_codes, is_admin

logging.basicConfig(level=logging.INFO)

def initialize_database():
    """Инициализация базы данных"""
    print("▶ Вызов init_db()...")
    try:
        init_db()
        print("✅ init_db() завершён")
    except Exception as e:
        print(f"❌ Ошибка при инициализации БД: {e}")
        traceback.print_exc()
        return False
    
    print("▶ Вызов init_items_db()...")
    try:
        init_items_db()
        print("✅ init_items_db() завершён")
    except Exception as e:
        print(f"❌ Ошибка init_items_db: {e}")
        return False
    
    seed_cities()
    seed_item_templates()
    seed_consumables()
    seed_hunter_quests()
    seed_tower_bosses()
    seed_herbs()
    seed_resources()
    seed_craft_recipes()
    seed_guild_quests()
    seed_premium_shop()
    
    print("✅ Все seed-данные загружены")
    return True

bot = Bot(token=TOKEN)

@bot.on.message()
async def message_handler(message: Message):
    user_id = message.peer_id
    text = message.text or ""
    payload = message.payload

    if payload:
        try:
            payload_dict = json.loads(payload)
            try:
                await handle_callback(bot.api, user_id, payload_dict)
            except Exception as e:
                print(f"❌ Ошибка в callback у пользователя {user_id}:")
                traceback.print_exc()
                await send_message(bot.api, user_id,
                    "⚠️ Произошла ошибка. Пожалуйста, сообщите разработчику.\n"
                    "Вы будете перенаправлены в город.")
                await show_city(bot.api, user_id)
            return
        except json.JSONDecodeError:
            pass

    if text:
        try:
            user_data = await get_user_async(user_id)
            state = user_data['state']
            
            text_input_states = [
                'awaiting_name', 'awaiting_gender', 'awaiting_guild_name',
                'awaiting_guild_donate', 'awaiting_guild_withdraw',
                'awaiting_tower_message', 'awaiting_guild_message',
                'awaiting_guild_manage_id', 'awaiting_auction_price',
                'awaiting_auction_buy_id', 'awaiting_mail_recipient',
                'awaiting_mail_subject', 'awaiting_mail_body',
                'awaiting_mail_attach_money', 'awaiting_mail_attach_qty',
                'awaiting_guild_apply', 'awaiting_guild_storage_remove',
                'awaiting_premium_buy', 'awaiting_code',
                'awaiting_inventory_equip_id', 'awaiting_inventory_unequip_id',
                'awaiting_tower_invite', 'scrolls'
            ]
            
            if state not in text_input_states:
                return

            # ---- ОБРАБОТКА ВВОДА ИМЕНИ ----
            if state == 'awaiting_name':
                name = text.strip()
                if len(name) < 2:
                    await send_message(bot.api, user_id, '❌ Имя должно быть длиннее 1 символа.')
                    return
                user_data = await get_user_async(user_id)
                context = user_data['context']
                gender = context.get('gender')
                if not gender:
                    await send_message(bot.api, user_id, '❌ Ошибка: пол не выбран. Начните заново.', get_back_keyboard('город'))
                    return
                await asyncio.to_thread(create_character, user_id, name, gender)
                await send_message(bot.api, user_id, f'🎉 Поздравляю, {name}!\nТы выбрал пол: {"♂ Мужской" if gender == "male" else "♀ Женский"}.\nТеперь ты в Стальном Троне.\n\nДостигни 20 уровня, чтобы выбрать класс в Ратуше.', get_back_keyboard('город'))
                await show_city(bot.api, user_id)
                return

            # ---- ПРЕМИУМ МАГАЗИН (ввод ID) ----
            if state == 'awaiting_premium_buy':
                try:
                    item_id = int(text.strip())
                    if item_id <= 0:
                        await send_message(bot.api, user_id, '❌ ID должен быть положительным числом.', get_back_keyboard('премиум магазин'))
                        return
                    from locations.premium import show_premium_buy_confirm
                    await show_premium_buy_confirm(bot.api, user_id, item_id)
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите число (ID товара).', get_back_keyboard('премиум магазин'))
                return

            # ---- СОЗДАНИЕ ГИЛЬДИИ ----
            if state == 'awaiting_guild_name':
                name = text.strip()
                if len(name) < 2 or len(name) > 30:
                    await send_message(bot.api, user_id, '❌ Название должно быть от 2 до 30 символов.')
                    return
                char = await get_character_async(user_id)
                if not char:
                    await send_message(bot.api, user_id, '❌ Сначала создайте персонажа.', get_back_keyboard('город'))
                    return
                guild_id, msg = await asyncio.to_thread(create_guild, char['id'], name)
                if guild_id:
                    await send_message(bot.api, user_id, f'✅ {msg}', get_back_keyboard('гильдию'))
                    await show_guild(bot.api, user_id)
                else:
                    await send_message(bot.api, user_id, f'❌ {msg}', get_back_keyboard('гильдию'))
                await update_user_async(user_id, state='city', context={})
                return

            # ---- ПОПОЛНЕНИЕ КАЗНЫ ГИЛЬДИИ ----
            if state == 'awaiting_guild_donate':
                try:
                    amount = int(text.strip())
                    if amount <= 0:
                        await send_message(bot.api, user_id, '❌ Сумма должна быть положительным числом.', get_back_keyboard('гильдию'))
                        return
                    char = await get_character_async(user_id)
                    if not char:
                        await send_message(bot.api, user_id, '❌ Сначала создайте персонажа.', get_back_keyboard('город'))
                        return
                    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
                    if not guild:
                        await send_message(bot.api, user_id, '❌ Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
                        return
                    if char['silver'] < amount:
                        await send_message(bot.api, user_id, f'❌ Недостаточно серебра! Нужно {amount}💰.', get_back_keyboard('гильдию'))
                        return
                    await show_guild_donate_confirm(bot.api, user_id, amount)
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите целое число (например, 100).', get_back_keyboard('гильдию'))
                return

            # ---- СНЯТИЕ ДЕНЕГ ИЗ КАЗНЫ ----
            if state == 'awaiting_guild_withdraw':
                try:
                    amount = int(text.strip())
                    if amount <= 0:
                        await send_message(bot.api, user_id, '❌ Сумма должна быть положительным числом.', get_back_keyboard('гильдию'))
                        return
                    char = await get_character_async(user_id)
                    if not char:
                        await send_message(bot.api, user_id, '❌ Сначала создайте персонажа.', get_back_keyboard('город'))
                        return
                    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
                    if not guild:
                        await send_message(bot.api, user_id, '❌ Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
                        return
                    if guild['leader_id'] != char['id']:
                        await send_message(bot.api, user_id, '❌ Только лидер может брать деньги из казны.', get_back_keyboard('гильдию'))
                        return
                    if guild['silver'] < amount:
                        await send_message(bot.api, user_id, f'❌ В казне недостаточно серебра! Доступно: {guild["silver"]}💰.', get_back_keyboard('гильдию'))
                        return
                    await show_guild_withdraw_confirm(bot.api, user_id, amount)
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите целое число (например, 100).', get_back_keyboard('гильдию'))
                return

            # ---- ЧАТ БАШНИ ----
            if state == 'awaiting_tower_message':
                char = await get_character_async(user_id)
                if not char:
                    await send_message(bot.api, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
                    await update_user_async(user_id, state='city', context={})
                    return
                party = await asyncio.to_thread(get_tower_party, char['id'])
                if not party:
                    await send_message(bot.api, user_id, 'Вы не в группе башни.', get_back_keyboard('город'))
                    await update_user_async(user_id, state='city', context={})
                    return
                await send_tower_chat_message(bot.api, party['id'], char['name'], text)
                await send_message(bot.api, user_id, '✅ Сообщение отправлено в чат группы!', get_tower_chat_keyboard())
                await update_user_async(user_id, state='tower_chat', context={'parent_state': 'tower'})
                return

            # ---- ЧАТ ГИЛЬДИИ ----
            if state == 'awaiting_guild_message':
                char = await get_character_async(user_id)
                if not char:
                    await send_message(bot.api, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
                    await update_user_async(user_id, state='city', context={})
                    return
                guild = await asyncio.to_thread(get_guild_by_character, char['id'])
                if not guild:
                    await send_message(bot.api, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('город'))
                    await update_user_async(user_id, state='city', context={})
                    return
                await send_guild_message(bot.api, char['id'], guild['id'], text)
                await send_message(bot.api, user_id, '✅ Сообщение отправлено в чат гильдии!', get_guild_chat_keyboard())
                await update_user_async(user_id, state='guild_chat', context={'parent_state': 'guild'})
                return

            # ---- УПРАВЛЕНИЕ ГИЛЬДИЕЙ ПО ID ----
            if state == 'awaiting_guild_manage_id':
                try:
                    member_id = int(text.strip())
                    if member_id <= 0:
                        await send_message(bot.api, user_id, '❌ ID должен быть положительным числом.', get_back_keyboard('гильдию'))
                        return
                    
                    char = await get_character_async(user_id)
                    if not char:
                        await send_message(bot.api, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
                        return
                    
                    guild = await asyncio.to_thread(get_guild_by_character, char['id'])
                    if not guild:
                        await send_message(bot.api, user_id, 'Вы не состоите в гильдии.', get_back_keyboard('гильдию'))
                        return
                    
                    members = get_guild_members(guild['id'])
                    target = None
                    for m in members:
                        if m['id'] == member_id:
                            target = m
                            break
                    
                    if not target:
                        await send_message(bot.api, user_id, f'❌ Участник с ID {member_id} не найден в гильдии.', get_back_keyboard('гильдию'))
                        return
                    
                    if target['id'] == char['id']:
                        await send_message(bot.api, user_id, '❌ Нельзя управлять самим собой.', get_back_keyboard('гильдию'))
                        return
                    
                    from locations.guild import show_guild_manage_member_by_id
                    await show_guild_manage_member_by_id(bot.api, user_id, member_id)
                    
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите число (ID участника).', get_back_keyboard('гильдию'))
                return

            # ---- ИЗЪЯТИЕ ПРЕДМЕТА СО СКЛАДА ----
            if state == 'awaiting_guild_storage_remove':
                try:
                    storage_id = int(text.strip())
                    from locations.guild import show_guild_storage_remove_confirm
                    await show_guild_storage_remove_confirm(bot.api, user_id, storage_id, 1)
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите число (ID предмета).', get_back_keyboard('гильдию'))
                return

            # ---- АУКЦИОН - ВВОД ЦЕНЫ ----
            if state == 'awaiting_auction_price':
                try:
                    price = int(text.strip())
                    if price <= 0:
                        await send_message(bot.api, user_id, '❌ Цена должна быть положительным числом.', get_back_keyboard('аукцион'))
                        return
                    user_data = await get_user_async(user_id)
                    context = user_data['context']
                    item_type = context.get('auction_item_type')
                    item_id = context.get('auction_item_id')
                    char = await get_character_async(user_id)
                    if not char:
                        await send_message(bot.api, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
                        return
                    from auction import create_auction_lot
                    lot_id, msg = create_auction_lot('player', char['id'], item_type, item_id, 1, price)
                    if lot_id:
                        await send_message(bot.api, user_id, f'✅ {msg}', get_back_keyboard('аукцион'))
                    else:
                        await send_message(bot.api, user_id, f'❌ {msg}', get_back_keyboard('аукцион'))
                    await update_user_async(user_id, state='auction', context={})
                    await show_auction(bot.api, user_id)
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите целое число (например, 100).', get_back_keyboard('аукцион'))
                return

            # ---- АУКЦИОН - ВВОД ID ЛОТА ----
            if state == 'awaiting_auction_buy_id':
                try:
                    lot_id = int(text.strip())
                    if lot_id <= 0:
                        await send_message(bot.api, user_id, '❌ ID должен быть положительным числом.', get_back_keyboard('аукцион'))
                        return
                    await show_auction_buy_confirm(bot.api, user_id, lot_id)
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите целое число (ID лота).', get_back_keyboard('аукцион'))
                return

            # ---- ПОЧТА - ПОЛУЧАТЕЛЬ ----
            if state == 'awaiting_mail_recipient':
                await show_mail_write_subject(bot.api, user_id, text.strip())
                return

            # ---- ПОЧТА - ТЕМА ----
            if state == 'awaiting_mail_subject':
                await show_mail_write_body(bot.api, user_id, text.strip())
                return

            # ---- ПОЧТА - ТЕЛО ----
            if state == 'awaiting_mail_body':
                await show_mail_send(bot.api, user_id, text)
                return

            # ---- ПОЧТА - ВЛОЖЕНИЕ ДЕНЕГ ----
            if state == 'awaiting_mail_attach_money':
                try:
                    amount = int(text.strip())
                    if amount <= 0:
                        await send_message(bot.api, user_id, '❌ Сумма должна быть положительным числом.', get_mail_keyboard())
                        return
                    char = await get_character_async(user_id)
                    if not char:
                        await send_message(bot.api, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
                        return
                    if char['silver'] < amount:
                        await send_message(bot.api, user_id, f'❌ Недостаточно серебра! Доступно: {char["silver"]}💰.', get_mail_keyboard())
                        return
                    
                    user_data = await get_user_async(user_id)
                    context = user_data['context']
                    
                    if not context.get('mail_recipient_id'):
                        await send_message(bot.api, user_id, '❌ Ошибка: получатель не найден. Попробуйте начать заново.', get_mail_keyboard())
                        return
                    if not context.get('mail_subject'):
                        await send_message(bot.api, user_id, '❌ Ошибка: тема письма не найдена. Попробуйте начать заново.', get_mail_keyboard())
                        return
                    
                    context['mail_attachment_type'] = 'money'
                    context['mail_attachment_silver'] = amount
                    context['mail_attachment_id'] = None
                    context['mail_attachment_qty'] = 0
                    await update_user_async(user_id, context=context)
                    
                    await show_mail_send_with_attachment(bot.api, user_id, context.get('mail_body', ''))
                    
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите целое число.', get_mail_keyboard())
                return

            # ---- ПОЧТА - КОЛИЧЕСТВО ДЛЯ ВЛОЖЕНИЯ ----
            if state == 'awaiting_mail_attach_qty':
                try:
                    qty = int(text.strip())
                    if qty <= 0:
                        await send_message(bot.api, user_id, '❌ Количество должно быть положительным числом.', get_mail_attachment_keyboard())
                        return
                    user_data = await get_user_async(user_id)
                    context = user_data['context']
                    
                    if not context.get('mail_recipient_id'):
                        await send_message(bot.api, user_id, '❌ Ошибка: получатель не найден. Попробуйте начать заново.', get_mail_keyboard())
                        return
                    if not context.get('mail_subject'):
                        await send_message(bot.api, user_id, '❌ Ошибка: тема письма не найдена. Попробуйте начать заново.', get_mail_keyboard())
                        return
                    
                    max_qty = context.get('mail_attachment_max', 0)
                    if qty > max_qty:
                        await send_message(bot.api, user_id, f'❌ У вас только {max_qty} шт.', get_mail_attachment_keyboard())
                        return
                    context['mail_attachment_qty'] = qty
                    await update_user_async(user_id, context=context)
                    await show_mail_send_with_attachment(bot.api, user_id, context.get('mail_body', ''))
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите целое число.', get_mail_attachment_keyboard())
                return

            # ---- ПРОМОКОДЫ ----
            if state == 'awaiting_code':
                from locations.codes import process_code_enter
                await process_code_enter(bot.api, user_id, text)
                return

            # ---- ИНВЕНТАРЬ - ЭКИПИРОВКА ПО ID ----
            if state == 'awaiting_inventory_equip_id':
                try:
                    item_id = int(text.strip())
                    from locations.inventory import show_inventory_equip_by_id
                    await show_inventory_equip_by_id(bot.api, user_id, item_id)
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите число (ID предмета).', get_back_keyboard('инвентарь'))
                return

            # ---- ИНВЕНТАРЬ - СНЯТИЕ ПО ID ----
            if state == 'awaiting_inventory_unequip_id':
                try:
                    item_id = int(text.strip())
                    if item_id <= 0:
                        await send_message(bot.api, user_id, '❌ ID должен быть положительным числом.', get_back_keyboard('инвентарь'))
                        return
                    
                    from core import get_equipment, unequip_item
                    char = await get_character_async(user_id)
                    if not char:
                        await send_message(bot.api, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
                        return
                    
                    equipment = get_equipment(char['id'])
                    
                    slot_found = None
                    item_name = None
                    for slot, item in equipment.items():
                        if item and item['id'] == item_id:
                            slot_found = slot
                            item_name = item.get('name', 'Предмет')
                            break
                    
                    if not slot_found:
                        await send_message(bot.api, user_id, f'❌ Предмет с ID {item_id} не найден в экипировке.', get_back_keyboard('инвентарь'))
                        return
                    
                    success = unequip_item(char['id'], slot_found)
                    if success:
                        from core import recalc_stats_async
                        await recalc_stats_async(char['id'])
                        await send_message(bot.api, user_id, f'✅ {item_name} снят в инвентарь!', get_back_keyboard('инвентарь'))
                    else:
                        await send_message(bot.api, user_id, '❌ Не удалось снять предмет.', get_back_keyboard('инвентарь'))
                    
                    from locations.inventory import show_inventory
                    await show_inventory(bot.api, user_id)
                    
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите число (ID предмета).', get_back_keyboard('инвентарь'))
                return

            # ---- БАШНЯ - ПРИГЛАШЕНИЕ ----
            if state == 'awaiting_tower_invite':
                try:
                    invited_id = int(text.strip())
                    if invited_id <= 0:
                        await send_message(bot.api, user_id, '❌ ID должен быть положительным числом.', get_back_keyboard('башня'))
                        return
                    
                    char = await get_character_async(user_id)
                    if not char:
                        await send_message(bot.api, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
                        return
                    
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    cur.execute('SELECT id, name FROM characters WHERE id = ?', (invited_id,))
                    invited_row = cur.fetchone()
                    conn.close()
                    
                    if not invited_row:
                        await send_message(bot.api, user_id, f'❌ Игрок с ID {invited_id} не найден.', get_back_keyboard('башня'))
                        await update_user_async(user_id, state='tower', context={'parent_state': 'meadow'})
                        return
                    
                    if invited_id == char['id']:
                        await send_message(bot.api, user_id, '❌ Нельзя пригласить самого себя.', get_back_keyboard('башня'))
                        await update_user_async(user_id, state='tower', context={'parent_state': 'meadow'})
                        return
                    
                    success, msg = await invite_to_tower_party(char['id'], invited_id)
                    await send_message(bot.api, user_id, f'{"✅" if success else "❌"} {msg}')
                    
                    await update_user_async(user_id, state='tower', context={'parent_state': 'meadow'})
                    
                    from locations.tower import show_tower
                    await show_tower(bot.api, user_id)
                    
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите число (ID игрока).', get_back_keyboard('башня'))
                    await update_user_async(user_id, state='tower', context={'parent_state': 'meadow'})
                return

        except Exception as e:
            print(f"❌ Ошибка в текстовом сообщении от {user_id}:")
            traceback.print_exc()
            await send_message(bot.api, user_id,
                "⚠️ Произошла ошибка. Пожалуйста, сообщите разработчику.\n"
                "Вы будете перенаправлены в город.")
            await show_city(bot.api, user_id)


async def main_loop():
    """Основной цикл с переподключением"""
    print("🚀 Запуск бота...")
    
    if not initialize_database():
        print("❌ Ошибка инициализации. Бот не запущен.")
        return
    
    asyncio.create_task(scheduler.run())
    
    while True:
        try:
            print("🔄 Подключение к VK API...")
            await bot.run_polling()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            traceback.print_exc()
            print("🔄 Переподключение через 15 секунд...")
            await asyncio.sleep(15)

async def main_loop():
    """Основной цикл с переподключением"""
    print("🚀 Запуск бота...")
    
    if not initialize_database():
        print("❌ Ошибка инициализации. Бот не запущен.")
        return
    
    asyncio.create_task(scheduler.run())
    
    while True:
        try:
            print("🔄 Подключение к VK API...")
            await bot.run_polling()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            traceback.print_exc()
            print("🔄 Переподключение через 15 секунд...")
            await asyncio.sleep(15)

async def main():
    await main_loop()

if __name__ == "__main__":
    asyncio.run(main())
