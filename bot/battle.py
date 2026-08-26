# battle.py
import random
import time
import sqlite3
import json
import asyncio
import traceback
from core import get_character, get_character_by_id, update_user, send_message, get_user, DB_NAME, get_player_consumables, use_consumable, apply_debuff, recalc_stats, get_character_async, update_user_async, get_user_async, recalc_stats_async
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from monsters import generate_monster
from utils import exp_to_next_level
from items import get_item_template_id_by_name, create_player_item, generate_shop_item
from guild import get_guild_by_character, guild_exp_to_next_level
from quests import update_quest_progress
from resources import drop_resource_for_monster, add_resource
from keyboards import get_graveyard_after_battle_keyboard, get_back_keyboard, get_after_battle_keyboard
from vip import get_vip, get_vip_bonus, VIP_NAMES, VIP_COLORS

FOREST_IMAGE = 'photo-240828623_456239316'
FOREST_DEEP_IMAGE = 'photo-240828623_456239315'
FOREST_WANDER_IMAGE = 'photo-240828623_456239317'
FOREST_EXIT_IMAGE = 'photo-240828623_456239316'
GRAVEYARD_IMAGE = 'photo-240828623_456239323'
GRAVEYARD_DEEP_IMAGE = 'photo-240828623_456239322'
GRAVEYARD_WANDER_IMAGE = 'photo-240828623_456239321'
TOWER_IMAGE = 'photo-240828623_456239325'

MATERIALS = ['Шкура', 'Коготь', 'Зуб', 'Магическая эссенция']

BOSS_LOOT_TEMPLATES = [
    {'slot': 'weapon_right', 'name': 'Меч'},
    {'slot': 'weapon_right', 'name': 'Кинжал'},
    {'slot': 'weapon_right', 'name': 'Посох'},
    {'slot': 'weapon_left', 'name': 'Щит'},
    {'slot': 'head', 'name': 'Шлем'},
    {'slot': 'armor', 'name': 'Кольчуга'},
    {'slot': 'boots', 'name': 'Сапоги'}
]

async def delay_with_message(vk, user_id, text, attachment=None, delay_range=(0, 0)):
    if delay_range and len(delay_range) == 2:
        delay = random.randint(delay_range[0], delay_range[1])
        await asyncio.sleep(delay)
    await send_message(vk, user_id, text, attachment=attachment)

def get_battle_keyboard(player_class):
    keyboard = VkKeyboard()
    keyboard.add_button('⚔ Атака', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'battle_attack'})
    keyboard.add_button('🛡 Защита (10% STA)', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'battle_defend'})
    keyboard.add_line()
    keyboard.add_button('🌀 Парирование', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'battle_parry'})
    if player_class == 'Оруженосец':
        keyboard.add_button('🛡 Стойка', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'battle_super'})
    elif player_class == 'Охотник':
        keyboard.add_button('🏹 Меткий выстрел', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'battle_super'})
    elif player_class == 'Послушник':
        keyboard.add_button('✨ Исцеление', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'battle_magic'})
    keyboard.add_line()
    keyboard.add_button('💊 Зелье', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'battle_potion'})
    keyboard.add_button('🏃 Сбежать', color=VkKeyboardColor.NEGATIVE, payload={'cmd': 'battle_flee'})
    return keyboard

def get_after_battle_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('🌲 В глубь леса', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'forest_deep'})
    keyboard.add_button('🚶 Побродить', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'forest_wander'})
    keyboard.add_line()
    keyboard.add_button('🚪 К выходу', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_exit'})
    return keyboard

async def start_battle(vk, user_id, zone, depth=0):
    print(f"⚔️ start_battle вызван: user_id={user_id}, zone={zone}, depth={depth}")
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.')
        return
    monster = generate_monster(zone, depth)
    if not monster:
        await send_message(vk, user_id, 'В этой зоне пока нет монстров.')
        return
    battle_state = {
        'monster': monster,
        'player_hp': char['hp'],
        'player_max_hp': char['max_hp'],
        'player_mana': char['mana'],
        'player_max_mana': char['max_mana'],
        'player_stamina': char['stamina'],
        'player_max_stamina': char['max_stamina'],
        'player_attack': char['attack'],
        'player_defense': char.get('defense', 0),
        'player_class': char['class'] or 'Неизвестный',
        'crit_chance': char['crit_chance'],
        'dodge_chance': char['dodge_chance'],
        'round': 0,
        'parry_charges': 4,  # 4 заряда = готово
        'counter_available': True,
        'shield': False,
        'shield_active': False,
        'shield_duration': 0,
        'parry_used_this_turn': False,
        'log': [],
        'zone': zone,
        'depth': depth
    }
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['battle'] = battle_state
    context['battle_active'] = True
    context['prev_state'] = user_data['state']
    await update_user_async(user_id, state='battle', context=context)
    await send_battle_status(vk, user_id)

async def send_battle_status(vk, user_id):
    user_data = await get_user_async(user_id)
    context = user_data['context']
    battle = context.get('battle')
    if not battle:
        return
    await send_battle_status_from_context(vk, user_id, context)

async def send_battle_status_from_context(vk, user_id, context):
    battle = context.get('battle')
    if not battle:
        return
    monster = battle['monster']
    log_text = "\n".join(battle['log'][-5:])
    if not log_text:
        log_text = "⚔️ Бой начинается!"
    
    # ПАРИРОВАНИЕ - новая логика с зарядами
    parry_charges = battle.get('parry_charges', 4)
    
    if parry_charges >= 4:
        parry_status = "✅ Готово"
    else:
        bar = "█" * parry_charges + "□" * (4 - parry_charges)
        parry_status = f"🔄 {bar} ({parry_charges}/4)"
    
    shield_status = "❌ Нет"
    if battle.get('shield_active'):
        duration = battle.get('shield_duration', 0)
        shield_status = f"🛡 Активна ({duration} ход.)" if duration > 0 else "🛡 Активна (последний ход!)"
    
    status = (
        f"⚔️ {monster['name']}\n"
        f"❤️ HP монстра: {monster['hp']}/{monster['max_hp']}\n"
        f"⚔️ Атака монстра: {monster['attack']}\n"
        f"📖 {monster.get('description', '')}\n\n"
        f"🧑 Вы:\n"
        f"❤️ HP: {battle['player_hp']}/{battle['player_max_hp']}\n"
        f"💧 Мана: {battle['player_mana']}/{battle['player_max_mana']}\n"
        f"⚡ Выносливость: {battle['player_stamina']}/{battle['player_max_stamina']}\n"
        f"⚔️ Атака: {battle['player_attack']}\n"
        f"🛡 Защита: {battle['player_defense']} {shield_status}\n"
        f"🌀 Парирование: {parry_status}\n\n"
        f"📜 Лог:\n{log_text}"
    )
    try:
        keyboard = get_battle_keyboard(battle['player_class'])
        await send_message(vk, user_id, status, keyboard, attachment=monster.get('image'))
    except Exception as e:
        print(f"DEBUG: Ошибка при отправке статуса: {e}")
        await send_message(vk, user_id, status, None, attachment=monster.get('image'))

async def show_battle_potions(vk, user_id):
    char = await get_character_async(user_id)
    if not char:
        return
    consumables = get_player_consumables(char['id'])
    if not consumables:
        await send_message(vk, user_id, 'У вас нет зелий!', get_battle_keyboard(char['class']))
        return
    keyboard = VkKeyboard()
    for c in consumables:
        label = f"{c['icon']} {c['name']} (x{c['quantity']})"
        keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'battle_use_potion', 'template_id': c['id']})
        keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'battle_back'})
    await send_message(vk, user_id, '💊 Выберите зелье для использования:', keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['battle_potion_menu'] = True
    await update_user_async(user_id, context=context)

async def process_battle_action(vk, user_id, action, payload=None):
    user_data = await get_user_async(user_id)
    context = user_data['context']
    
    if context.get('battle_potion_menu'):
        if action == 'use_potion' or action == 'battle_use_potion':
            template_id = payload.get('template_id') if payload else None
            if not template_id:
                await send_message(vk, user_id, 'Ошибка: не выбран шаблон зелья.')
                return
            char = await get_character_async(user_id)
            if not char:
                return
            effect, error = use_consumable(char['id'], template_id)
            if error:
                await send_message(vk, user_id, f'❌ {error}', get_battle_keyboard(char['class']))
                return
            restore_type, percent = effect
            battle = context.get('battle')
            if not battle:
                return
            if restore_type == 'hp':
                restore = round(battle['player_max_hp'] * percent / 100)
                battle['player_hp'] = min(battle['player_max_hp'], battle['player_hp'] + restore)
                log = f"💊 Вы восстановили {restore} HP."
            elif restore_type == 'mana':
                restore = round(battle['player_max_mana'] * percent / 100)
                battle['player_mana'] = min(battle['player_max_mana'], battle['player_mana'] + restore)
                log = f"💊 Вы восстановили {restore} маны."
            elif restore_type == 'stamina':
                restore = round(battle['player_max_stamina'] * percent / 100)
                battle['player_stamina'] = min(battle['player_max_stamina'], battle['player_stamina'] + restore)
                log = f"💊 Вы восстановили {restore} выносливости."
            battle['log'].append(log)
            context.pop('battle_potion_menu', None)
            await update_user_async(user_id, context=context)
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute('UPDATE characters SET hp=?, mana=?, stamina=? WHERE id=?', 
                        (battle['player_hp'], battle['player_mana'], battle['player_stamina'], char['id']))
            conn.commit()
            conn.close()
            await send_battle_status(vk, user_id)
            return
        elif action == 'back':
            context.pop('battle_potion_menu', None)
            await update_user_async(user_id, context=context)
            await send_battle_status(vk, user_id)
            return
        else:
            return

    if not context.get('battle_active'):
        return
    battle = context.get('battle')
    if not battle:
        return
    monster = battle['monster']
    player_class = battle['player_class']
    battle['parry_used_this_turn'] = False
    battle['round'] += 1

    # Обработка действий
    if action == 'attack':
        damage = battle['player_attack'] + random.randint(-2, 3) - monster['defense']
        damage = max(1, damage)
        if random.random() * 100 < battle.get('crit_chance', 0):
            damage = int(damage * 1.5)
            battle['log'].append(f"💥 КРИТИЧЕСКИЙ УДАР! {damage} урона.")
        else:
            battle['log'].append(f"⚔️ Вы нанесли {damage} урона.")
        monster['hp'] -= damage
        
        # Пополняем заряд парирования после атаки
        battle['parry_charges'] = min(4, battle.get('parry_charges', 0) + 1)
        
    elif action == 'defend':
        cost = max(1, int(battle['player_max_stamina'] * 0.1))
        if battle['player_stamina'] < cost:
            battle['log'].append(f"❌ Недостаточно выносливости! Нужно {cost} (у вас {battle['player_stamina']}).")
            await save_battle_and_send(vk, user_id, context)
            return
        battle['player_stamina'] -= cost
        battle['shield'] = True
        battle['shield_active'] = True
        battle['shield_duration'] = 3
        battle['log'].append(f"🛡 Вы встали в защитную стойку на 3 хода (потрачено {cost} выносливости).")
        
        # Пополняем заряд парирования после защиты
        battle['parry_charges'] = min(4, battle.get('parry_charges', 0) + 1)
        
    elif action == 'parry':
        # Проверяем, есть ли заряды (4 = готово)
        if battle.get('parry_charges', 0) < 4:
            battle['log'].append("🌀 Парирование ещё не готово.")
            await save_battle_and_send(vk, user_id, context)
            return
        
        # Контратака
        counter_damage = int(battle['player_attack'] * 0.8) + random.randint(0, 2)
        monster['hp'] -= counter_damage
        battle['log'].append(f"🌀 Парирование! Контратака на {counter_damage} урона.")
        
        # Сбрасываем заряды в 0
        battle['parry_charges'] = 0
        battle['counter_available'] = False
        battle['parry_used_this_turn'] = True
        
        await save_battle_and_send(vk, user_id, context)
        return
        
    elif action == 'super':
        if battle['player_stamina'] < 10:
            battle['log'].append("❌ Недостаточно выносливости (нужно 10).")
            await save_battle_and_send(vk, user_id, context)
            return
        battle['player_stamina'] -= 10
        super_damage = battle['player_attack'] * 2 + random.randint(0, 5)
        monster['hp'] -= super_damage
        battle['log'].append(f"🔥 Суперудар! {super_damage} урона.")
        
        # Пополняем заряд парирования после суперудара
        battle['parry_charges'] = min(4, battle.get('parry_charges', 0) + 1)
        
    elif action == 'magic':
        if battle['player_mana'] < 5:
            battle['log'].append("❌ Недостаточно маны.")
            await save_battle_and_send(vk, user_id, context)
            return
        battle['player_mana'] -= 5
        heal = random.randint(15, 30)
        battle['player_hp'] = min(battle['player_max_hp'], battle['player_hp'] + heal)
        battle['log'].append(f"✨ Исцеление: +{heal} HP.")
        
        # Пополняем заряд парирования после магии
        battle['parry_charges'] = min(4, battle.get('parry_charges', 0) + 1)
        
    elif action == 'potion':
        await show_battle_potions(vk, user_id)
        return
        
    elif action == 'flee':
        if random.random() < 0.3:
            battle['log'].append("🏃 Вы сбежали!")
            await end_battle(vk, user_id, won=False, fled=True)
            return
        else:
            battle['log'].append("🏃 Попытка побега не удалась.")
            await monster_attacks(vk, user_id, battle)
            await save_battle_and_send(vk, user_id, context)
            return
            
    else:
        battle['log'].append("❓ Неизвестное действие.")
        await save_battle_and_send(vk, user_id, context)
        return

    # Проверка на победу
    if monster['hp'] <= 0:
        await asyncio.sleep(0.5)
        await end_battle(vk, user_id, won=True)
        return
    
    # Атака монстра
    await monster_attacks(vk, user_id, battle)
    await save_battle_and_send(vk, user_id, context)

async def monster_attacks(vk, user_id, battle):
    monster = battle['monster']
    monster_attack = monster['attack']
    player_defense = battle['player_defense']
    shield_active = battle.get('shield', False)
    absorbed = 0

    if shield_active and battle.get('shield_duration', 0) > 0:
        effective_defense = player_defense * 2
        battle['shield_active'] = True
        battle['shield_duration'] -= 1
        if battle['shield_duration'] <= 0:
            battle['shield'] = False
            battle['shield_active'] = False
            battle['log'].append("🛡 Защита закончилась.")
    else:
        effective_defense = player_defense
        battle['shield_active'] = False

    raw_damage = monster_attack + random.randint(-2, 2) - effective_defense
    damage = max(1, raw_damage)
    
    if random.random() * 100 < battle.get('dodge_chance', 0):
        battle['log'].append("💨 Вы уклонились от атаки!")
        return

    if shield_active and battle.get('shield_duration', 0) >= 0:
        raw_without_shield = monster_attack + random.randint(-2, 2) - player_defense
        without_shield = max(1, raw_without_shield)
        absorbed = without_shield - damage
        if absorbed > 0:
            battle['log'].append(f"🛡 Защита поглотила {absorbed} урона.")
        else:
            battle['log'].append("🛡 Защита активна, но урон минимален.")

    battle['player_hp'] -= damage
    battle['log'].append(f"💢 Монстр нанёс {damage} урона.")

    if battle['player_hp'] <= 0:
        battle['shield'] = False
        battle['shield_active'] = False

async def save_battle_and_send(vk, user_id, context):
    battle = context.get('battle')
    if not battle:
        return
    if battle['player_hp'] <= 0:
        await end_battle(vk, user_id, won=False)
        return
    if battle['monster']['hp'] <= 0:
        await end_battle(vk, user_id, won=True)
        return
    await update_user_async(user_id, context=context)
    await send_battle_status_from_context(vk, user_id, context)

async def check_player_level_up(character_id):
    return await asyncio.to_thread(_check_player_level_up_sync, character_id)

def _check_player_level_up_sync(character_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT level, exp, max_hp, hp, attack, defense, max_mana, mana, max_stamina, stamina FROM characters WHERE id = ?', (character_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    level, exp, max_hp, hp, attack, defense, max_mana, mana, max_stamina, stamina = row
    leveled = False
    while exp >= exp_to_next_level(level):
        needed = exp_to_next_level(level)
        exp -= needed
        level += 1
        leveled = True
        max_hp += 10
        hp = max_hp
        attack += 2
        defense += 1
        max_mana += 5
        mana = max_mana
        max_stamina += 3
        stamina = max_stamina
    if leveled:
        cur.execute('''UPDATE characters 
                       SET level=?, exp=?, max_hp=?, hp=?, attack=?, defense=?, 
                           max_mana=?, mana=?, max_stamina=?, stamina=?
                       WHERE id=?''',
                    (level, exp, max_hp, hp, attack, defense, max_mana, mana, max_stamina, stamina, character_id))
        conn.commit()
        recalc_stats(character_id)
    conn.close()
    return leveled

async def end_battle(vk, user_id, won, fled=False):
    from locations import show_city, show_exit, show_church

    try:
        user_data = await get_user_async(user_id)
        context = user_data['context']
        battle = context.get('battle')
        if not battle:
            print("❌ end_battle: battle не найден в контексте")
            await send_message(vk, user_id, "Ошибка: состояние боя потеряно. Возвращаемся в город.")
            await show_city(vk, user_id)
            return
        char = await get_character_async(user_id)
        if not char:
            await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
            return
        zone = battle['zone']
        depth = battle.get('depth', 0)

        if fled:
            result_text = "🏃 Вы сбежали из боя."
            context.pop('battle', None)
            context.pop('battle_active', None)
            await update_user_async(user_id, context=context)
            await send_message(vk, user_id, result_text, get_back_keyboard('город'))
            await show_exit(vk, user_id)
            return

        if won:
            exp_gain = battle['monster']['exp']
            silver_gain = battle['monster']['silver']
            tier = battle['monster'].get('tier', 1)
            is_boss = battle['monster'].get('is_boss', False)
            drop_chance = battle['monster'].get('drop_chance', 0.25)

            quest_completed = False
            try:
                quest_completed = update_quest_progress(char['id'], battle['monster']['name'], 1)
                if quest_completed:
                    print("✅ Квест охотника выполнен!")
            except Exception as e:
                print(f"⚠️ Ошибка обновления квеста: {e}")
                traceback.print_exc()

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # VIP бонус
            from vip import get_vip, get_vip_bonus, VIP_NAMES, VIP_COLORS
            vip_level, _ = get_vip(char['id'])
            vip_text = ""
            exp_bonus = 0
            silver_bonus = 0
            
            if vip_level > 0:
                bonus = get_vip_bonus(vip_level)
                exp_bonus = int(exp_gain * bonus['exp'] / 100)
                silver_bonus = int(silver_gain * bonus['silver'] / 100)
                exp_gain += exp_bonus
                silver_gain += silver_bonus
                
                vip_icon = VIP_COLORS.get(vip_level, '')
                vip_name = VIP_NAMES.get(vip_level, '')
                vip_text = f"\n👑 VIP {vip_name} (+{bonus['exp']}%): +{exp_bonus} опыта, +{silver_bonus} серебра"

            char['exp'] += exp_gain
            char['silver'] += silver_gain

            drop = drop_resource_for_monster(zone, tier, is_boss, drop_chance)
            drop_text = ""
            if drop:
                resource_id, quantity = drop
                add_resource(char['id'], resource_id, quantity)
                conn_res = sqlite3.connect(DB_NAME)
                cur_res = conn_res.cursor()
                cur_res.execute('SELECT name, icon FROM resource_templates WHERE id = ?', (resource_id,))
                res = cur_res.fetchone()
                conn_res.close()
                if res:
                    drop_text = f"\n🎁 Вы получили ресурс: {res[1]} {res[0]} x{quantity}!"

            chest_text = ""
            if zone == 'graveyard':
                from graveyard import check_graveyard_chest
                chest = check_graveyard_chest()
                if chest:
                    if chest['type'] == 'silver':
                        char['silver'] += chest['amount']
                        chest_text = f"\n{chest['text']}"
                    elif chest['type'] == 'item':
                        item_templates = ['Меч', 'Кинжал', 'Посох', 'Щит', 'Шлем', 'Кольчуга', 'Сапоги']
                        template_name = random.choice(item_templates)
                        item_level = max(1, depth // 2 + 1)
                        item_id = generate_shop_item(char['id'], template_name, item_level)
                        if item_id:
                            conn_upd = sqlite3.connect(DB_NAME)
                            cur_upd = conn_upd.cursor()
                            cur_upd.execute('UPDATE player_items SET rarity = ? WHERE id = ?', (chest['rarity'], item_id))
                            conn_upd.commit()
                            conn_upd.close()
                            rarity_name = {1: 'зелёный', 2: 'синий', 3: 'фиолетовый'}.get(chest['rarity'], 'зелёный')
                            chest_text = f"\n{chest['text']} ({template_name}, {rarity_name}, уровень {item_level})"

            char['hp'] = battle['player_hp']
            char['mana'] = battle['player_mana']
            char['stamina'] = battle['player_stamina']

            cur.execute('''UPDATE characters 
                           SET level=?, exp=?, silver=?, hp=?, max_hp=?, attack=?, defense=?, 
                               max_mana=?, mana=?, max_stamina=?, stamina=?, trophies=? 
                           WHERE id=?''',
                        (char['level'], char['exp'], char['silver'], char['hp'], char['max_hp'], 
                         char['attack'], char['defense'], char['max_mana'], char['mana'], 
                         char['max_stamina'], char['stamina'], char.get('trophies', 0), char['id']))

            guild = await asyncio.to_thread(get_guild_by_character, char['id'])
            if guild:
                guild_exp = max(1, exp_gain // 5)
                cur.execute('UPDATE characters SET guild_exp_contributed = guild_exp_contributed + ? WHERE id = ?', (guild_exp, char['id']))
                cur.execute('SELECT level, exp FROM guilds WHERE id = ?', (guild['id'],))
                g_row = cur.fetchone()
                if g_row:
                    g_level, g_exp = g_row
                    g_exp += guild_exp
                    while True:
                        needed = guild_exp_to_next_level(g_level)
                        if g_exp >= needed:
                            g_exp -= needed
                            g_level += 1
                            cur.execute('UPDATE guilds SET max_members = max_members + 3 WHERE id = ?', (guild['id'],))
                        else:
                            break
                    cur.execute('UPDATE guilds SET level = ?, exp = ? WHERE id = ?', (g_level, g_exp, guild['id']))

            conn.commit()
            conn.close()

            leveled = await check_player_level_up(char['id'])
            if leveled:
                char = await get_character_async(user_id)

            result_text = (
                f"⚔️ Победа!\n"
                f"Вы убили {battle['monster']['name']}!\n"
                f"Получено опыта: {exp_gain}\n"
                f"Получено серебра: {silver_gain}\n"
                f"{vip_text}\n"
                f"{drop_text}{chest_text}\n"
                f"Вы находитесь на глубине {depth}"
            )

        else:
            apply_debuff(char['id'], 1)
            char = await get_character_async(user_id)
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute('UPDATE characters SET hp = max_hp / 2, mana = max_mana / 2, stamina = max_stamina / 2 WHERE id = ?', (char['id'],))
            conn.commit()
            conn.close()
            result_text = f"💀 Поражение...\nВы пали в бою с {battle['monster']['name']}.\nВаше тело перенесено в Собор.\nНа вас наложено Проклятие (-30% к статам). Снимите его за 1000💰."
            context.pop('battle', None)
            context.pop('battle_active', None)
            await update_user_async(user_id, context=context)
            await send_message(vk, user_id, result_text, get_back_keyboard('собор'))
            await show_church(vk, user_id)
            return

        context.pop('battle', None)
        context.pop('battle_active', None)
        await update_user_async(user_id, context=context)

        if zone == 'forest':
            context = user_data['context']
            context['forest_depth'] = depth
            await update_user_async(user_id, context=context)
            print(f"🏆 Победа в лесу, сохранена глубина: {depth}")
            await send_message(vk, user_id, result_text, get_after_battle_keyboard())
            user_data = await get_user_async(user_id)
            context = user_data['context']
            context['parent_state'] = 'exit'
            await update_user_async(user_id, state='forest_after', context=context)
        elif zone == 'graveyard':
            context = user_data['context']
            context['graveyard_depth'] = depth
            await update_user_async(user_id, context=context)
            await send_message(vk, user_id, result_text, get_graveyard_after_battle_keyboard())
            user_data = await get_user_async(user_id)
            context = user_data['context']
            context['parent_state'] = 'exit'
            await update_user_async(user_id, state='graveyard_after', context=context)
        else:
            await send_message(vk, user_id, result_text, get_back_keyboard('город'))
            await show_exit(vk, user_id)
    except Exception as e:
        print(f"❌ Ошибка в end_battle для пользователя {user_id}:")
        traceback.print_exc()
        await send_message(vk, user_id, f"⚠️ Ошибка завершения боя: {e}\nВы будете перенаправлены в город.")
        await show_city(vk, user_id)