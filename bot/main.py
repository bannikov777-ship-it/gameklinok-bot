# main.py
import sys
import os
# Добавляем текущую папку в путь поиска модулей
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
from core.database import seed_cities, seed_consumables, seed_herbs, seed_guild_quests
from items import init_items_db, seed_item_templates
from resources import seed_resources
from crafting import seed_craft_recipes
from quests import seed_hunter_quests
from tower import seed_tower_bosses, get_tower_party, send_tower_chat_message
from guild import create_guild, get_guild_by_character, send_guild_message
from scheduler import scheduler
from locations import (handle_callback, show_city, show_guild, show_tower,
                       show_market, show_healer, show_auction, show_smithy,
                       show_church, show_market_shop, show_hunters, show_tavern,
                       show_town_hall, show_profile, show_inventory, show_exit,
                       show_forest, show_graveyard, show_meadow, show_rating,
                       show_guild_donate, show_guild_withdraw, show_guild_donate_confirm,
                       show_guild_withdraw_confirm, show_guild_members, show_guild_storage,
                       show_guild_stats, show_guild_manage, show_guild_manage_member,
                       show_guild_chat, show_hunters_quests, show_hunters_my_quests,
                       show_hunters_take_quest, show_hunters_sell, show_hunters,
                       show_healer_buy, show_healer_craft, show_healer_sell_herbs,
                       show_smithy_upgrade_menu, show_tavern_food, show_tavern_room,
                       show_church_remove_debuff, show_inventory_equip, show_inventory_unequip,
                       show_inventory_equip_select, show_tower_chat, show_auction_buy_confirm)
from handlers import handle_battle_action, show_mail, show_mail_read, show_mail_delete, show_mail_write
from keyboards import (get_gender_keyboard, get_back_keyboard, get_lore_keyboard, 
                       get_tower_chat_keyboard, get_guild_chat_keyboard)

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
    
    print("✅ Все seed-данные загружены")
    return True

bot = Bot(token=TOKEN)

@bot.on.message()
async def message_handler(message: Message):
    user_id = message.peer_id
    text = message.text or ""
    payload = message.payload

    # Обработка callback (кнопок)
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

    # Обработка текстовых сообщений ТОЛЬКО в определенных состояниях
    if text:
        try:
            user_data = await get_user_async(user_id)
            state = user_data['state']
            
            # Список состояний, в которых мы ожидаем ввод текста
            text_input_states = [
                'awaiting_name',              # ввод имени персонажа
                'awaiting_gender',            # выбор пола (обрабатывается через кнопки)
                'awaiting_guild_name',        # ввод названия гильдии
                'awaiting_guild_donate',      # ввод суммы для пополнения казны
                'awaiting_guild_withdraw',    # ввод суммы для снятия из казны
                'awaiting_tower_message',     # ввод сообщения в чат башни
                'awaiting_guild_message',     # ввод сообщения в чат гильдии
                'awaiting_auction_price',     # ввод цены на аукционе
                'awaiting_auction_buy_id',    # ввод ID лота для покупки
                'awaiting_mail_recipient',    # ввод получателя письма
                'awaiting_mail_subject',      # ввод темы письма
                'awaiting_mail_body',         # ввод тела письма
                'awaiting_mail_attach_money', # ввод суммы для вложения
                'awaiting_mail_attach_qty',   # ввод количества для вложения
            ]
            
            # Если состояние НЕ в списке ожидаемых - игнорируем сообщение
            if state not in text_input_states:
                # Просто игнорируем, ничего не отправляем
                return

                        # ---- ТЕСТОВЫЕ КОМАНДЫ ----
            if text.lower() == '!level':
                char = await get_character_async(user_id)
                if char:
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    cur.execute('UPDATE characters SET level = level + 1, exp = 0 WHERE id = ?', (char['id'],))
                    conn.commit()
                    conn.close()
                    await send_message(bot.api, user_id, f'⬆️ Уровень повышен до {char["level"] + 1}!')
                    await recalc_stats_async(char['id'])
                    await show_profile(bot.api, user_id)
                return

            if text.lower() == '!silver':
                char = await get_character_async(user_id)
                if char:
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    cur.execute('UPDATE characters SET silver = silver + 10000 WHERE id = ?', (char['id'],))
                    conn.commit()
                    conn.close()
                    await send_message(bot.api, user_id, '💰 Получено 10000 серебра!')
                    await show_profile(bot.api, user_id)
                return

            if text.lower() == '!max':
                char = await get_character_async(user_id)
                if char:
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    cur.execute('''
                        UPDATE characters 
                        SET level = 50, exp = 0, silver = 999999, crystals = 500,
                            hp = 1000, max_hp = 1000, mana = 500, max_mana = 500,
                            stamina = 300, max_stamina = 300, attack = 100, defense = 50,
                            crit_chance = 30, dodge_chance = 20, debuff = 0
                        WHERE id = ?
                    ''', (char['id'],))
                    conn.commit()
                    conn.close()
                    await recalc_stats_async(char['id'])
                    await send_message(bot.api, user_id, '💪 Персонаж максимально прокачан!')
                    await show_profile(bot.api, user_id)
                return

            # ---- ОБРАБОТКА ВВОДА ИМЕНИ ----
            if state == 'awaiting_name':
                name = text.strip()
                if len(name) < 2:
                    await send_message(bot.api, user_id, '❌ Имя должно быть длиннее 1 символа.')
                    return
                context = {'name': name}
                await update_user_async(user_id, state='awaiting_gender', context=context)
                await send_message(bot.api, user_id, f'Отлично, {name}! Теперь выбери пол:', get_gender_keyboard())
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

            # ---- ЧАТ БАШНИ (ввод сообщения) ----
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

            # ---- ЧАТ ГИЛЬДИИ (ввод сообщения) ----
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
                from handlers.mail import show_mail_write_subject
                await show_mail_write_subject(bot.api, user_id, text.strip())
                return

            # ---- ПОЧТА - ТЕМА ----
            if state == 'awaiting_mail_subject':
                from handlers.mail import show_mail_write_body
                await show_mail_write_body(bot.api, user_id, text.strip())
                return

            # ---- ПОЧТА - ТЕЛО ----
            if state == 'awaiting_mail_body':
                from handlers.mail import show_mail_send
                await show_mail_send(bot.api, user_id, text)
                return

            # ---- ПОЧТА - ВЛОЖЕНИЕ ДЕНЕГ ----
            if state == 'awaiting_mail_attach_money':
                try:
                    amount = int(text.strip())
                    if amount <= 0:
                        await send_message(bot.api, user_id, '❌ Сумма должна быть положительным числом.', get_back_keyboard('почту'))
                        return
                    char = await get_character_async(user_id)
                    if not char:
                        await send_message(bot.api, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
                        return
                    if char['silver'] < amount:
                        await send_message(bot.api, user_id, f'❌ Недостаточно серебра! Доступно: {char["silver"]}💰.', get_back_keyboard('почту'))
                        return
                    user_data = await get_user_async(user_id)
                    context = user_data['context']
                    context['mail_attachment_type'] = 'money'
                    context['mail_attachment_silver'] = amount
                    context['mail_attachment_id'] = None
                    context['mail_attachment_qty'] = 0
                    await update_user_async(user_id, context=context)
                    from handlers.mail import show_mail_send_with_attachment
                    body = context.get('mail_body')
                    await show_mail_send_with_attachment(bot.api, user_id, body)
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите целое число.', get_back_keyboard('почту'))
                return

            # ---- ПОЧТА - КОЛИЧЕСТВО ДЛЯ ВЛОЖЕНИЯ ----
            if state == 'awaiting_mail_attach_qty':
                try:
                    qty = int(text.strip())
                    if qty <= 0:
                        await send_message(bot.api, user_id, '❌ Количество должно быть положительным числом.', get_back_keyboard('почту'))
                        return
                    user_data = await get_user_async(user_id)
                    context = user_data['context']
                    max_qty = context.get('mail_attachment_max', 0)
                    if qty > max_qty:
                        await send_message(bot.api, user_id, f'❌ У вас только {max_qty} шт.', get_back_keyboard('почту'))
                        return
                    context['mail_attachment_qty'] = qty
                    await update_user_async(user_id, context=context)
                    from handlers.mail import show_mail_send_with_attachment
                    body = context.get('mail_body')
                    await show_mail_send_with_attachment(bot.api, user_id, body)
                except ValueError:
                    await send_message(bot.api, user_id, '❌ Введите целое число.', get_back_keyboard('почту'))
                return

        except Exception as e:
            print(f"❌ Ошибка в текстовом сообщении от {user_id}:")
            traceback.print_exc()
            await send_message(bot.api, user_id,
                "⚠️ Произошла ошибка. Пожалуйста, сообщите разработчику.\n"
                "Вы будете перенаправлены в город.")
            await show_city(bot.api, user_id)
    # Если текст есть, но состояние не в списке - просто игнорируем

async def handle_main(vk, user_id, text):
    """Основной обработчик сообщений (вызывается только из callback)"""
    # Эта функция больше не нужна, так как текстовые сообщения обрабатываются в message_handler
    pass

async def main():
    if not initialize_database():
        print("❌ Ошибка инициализации. Бот не запущен.")
        return
    asyncio.create_task(scheduler.run())
    await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())