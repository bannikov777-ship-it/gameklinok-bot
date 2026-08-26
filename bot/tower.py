# tower.py
import sqlite3
import json
import random
import time
import asyncio
from config import DB_NAME
from core import get_character, get_character_by_id, send_message, recalc_stats, update_user, get_character_async, get_character_by_id_async, recalc_stats_async, update_user_async
from utils import exp_to_next_level
from guild import get_guild_by_character, send_guild_message

TOWER_BOSSES = [
    # name, hp, attack, defense, exp, silver, image
    {'name': 'Глиняный Архивариус', 'hp': 400, 'attack': 25, 'defense': 5, 'exp': 100, 'silver': 200, 'image': 'photo-240828623_456239299'},
    {'name': 'Ржавый Сенешаль', 'hp': 600, 'attack': 28, 'defense': 10, 'exp': 200, 'silver': 250, 'image': 'photo-240828623_456239291'},
    {'name': 'Медуза Пустошей', 'hp': 800, 'attack': 31, 'defense': 15, 'exp': 300, 'silver': 300, 'image': 'photo-240828623_456239300'},
    {'name': 'Громовой Костолом', 'hp': 1000, 'attack': 34, 'defense': 20, 'exp': 400, 'silver': 350, 'image': 'photo-240828623_456239292'},
    {'name': 'Немой Клирик', 'hp': 1500, 'attack': 39, 'defense': 25, 'exp': 500, 'silver': 800, 'image': 'photo-240828623_456239294'},
    {'name': 'Хрустальный Мясник', 'hp': 2000, 'attack': 49, 'defense': 30, 'exp': 600, 'silver': 950, 'image': 'photo-240828623_456239295'},
    {'name': 'Страж Пепельного Договора', 'hp': 2200, 'attack': 57, 'defense': 35, 'exp': 700, 'silver': 1100, 'image': 'photo-240828623_456239296'},
    {'name': 'Гидра Обломков', 'hp': 2500, 'attack': 65, 'defense': 40, 'exp': 800, 'silver': 1250, 'image': 'photo-240828623_456239293'},
    {'name': 'Последний Монарх', 'hp': 2800, 'attack': 73, 'defense': 45, 'exp': 900, 'silver': 1400, 'image': 'photo-240828623_456239298'},
    {'name': 'Безликий Архимаг', 'hp': 3000, 'attack': 80, 'defense': 50, 'exp': 1000, 'silver': 1550, 'image': 'photo-240828623_456239297'},
]

def seed_tower_bosses():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM tower_bosses')
    if cur.fetchone()[0] == 0:
        for floor, boss in enumerate(TOWER_BOSSES, start=1):
            cur.execute('''
                INSERT INTO tower_bosses (floor, name, base_hp, base_attack, base_defense, exp_reward, silver_reward)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (floor, boss['name'], boss['hp'], boss['attack'], boss['defense'], boss['exp'], boss['silver']))
        conn.commit()
    conn.close()

def get_tower_boss(floor):
    if 1 <= floor <= len(TOWER_BOSSES):
        boss = TOWER_BOSSES[floor-1].copy()
        boss['max_hp'] = boss['hp']
        return boss
    return None

async def create_tower_party(vk, leader_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM tower_party WHERE leader_id = ?', (leader_id,))
    row = cur.fetchone()
    if row:
        party_id = row[0]
        cur.execute('''
            UPDATE tower_party
            SET members = ?, current_floor = 1, active = 1, current_boss = '{}'
            WHERE id = ?
        ''', (json.dumps([leader_id]), party_id))
        conn.commit()
        conn.close()
        await _send_guild_invite(vk, leader_id)
        await send_tower_chat_message(vk, party_id, "Система", "🏰 Группа восстановлена! Ожидайте участников.")
        return True, f"✅ Группа восстановлена! Вы лидер.\n📌 Ваш ID: {leader_id}"
    else:
        cur.execute('''
            INSERT INTO tower_party (leader_id, members, current_floor, active)
            VALUES (?, ?, 1, 1)
        ''', (leader_id, json.dumps([leader_id])))
        party_id = cur.lastrowid
        conn.commit()
        conn.close()
        await _send_guild_invite(vk, leader_id)
        await send_tower_chat_message(vk, party_id, "Система", "🏰 Группа создана! Ожидайте участников.")
        return True, f"✅ Группа создана! Вы лидер.\n📌 Ваш ID: {leader_id}"

async def invite_to_tower_party(vk, leader_id, invited_id):
    """Пригласить игрока в группу башни"""
    from vk_api.keyboard import VkKeyboard, VkKeyboardColor
    
    # Проверяем, существует ли группа
    party = get_tower_party(leader_id)
    if not party:
        return False, "Группа не найдена."
    
    if party['leader_id'] != leader_id:
        return False, "Только лидер может приглашать."
    
    if len(party['members']) >= 5:
        return False, "Группа заполнена (макс. 5)."
    
    # Получаем данные приглашаемого
    invited_char = get_character_by_id(invited_id)
    if not invited_char:
        return False, "Игрок не найден."
    
    # Проверяем, не в группе ли уже
    if invited_id in party['members']:
        return False, "Игрок уже в группе."
    
    # Проверяем, не в другой ли группе
    existing_party = get_tower_party(invited_id)
    if existing_party:
        return False, "Игрок уже состоит в другой группе."
    
    # Создаем клавиатуру для приглашения
    keyboard = VkKeyboard()
    keyboard.add_button('✅ Присоединиться', color=VkKeyboardColor.POSITIVE,
                        payload={'cmd': 'tower_accept_invite', 'leader_id': leader_id})
    keyboard.add_button('❌ Отказаться', color=VkKeyboardColor.NEGATIVE,
                        payload={'cmd': 'tower_decline_invite', 'leader_id': leader_id})
    
    leader_char = get_character_by_id(leader_id)
    
    # Отправляем приглашение
    try:
        await send_message(vk, invited_char['vk_id'],
                          f"🏰 {leader_char['name']} приглашает вас в группу Башни!\n"
                          f"📍 Текущий этаж: {party['current_floor']}\n"
                          f"👥 Состав: {len(party['members'])}/5",
                          keyboard)
        return True, f"Приглашение отправлено игроку {invited_char['name']}"
    except Exception as e:
        return False, f"Не удалось отправить приглашение: {str(e)}"

async def _send_guild_invite(vk, leader_id):
    from vk_api.keyboard import VkKeyboard, VkKeyboardColor
    char = get_character_by_id(leader_id)
    if not char:
        return
    guild = get_guild_by_character(leader_id)
    if not guild:
        return
    keyboard = VkKeyboard()
    keyboard.add_button('🏰 Присоединиться', color=VkKeyboardColor.POSITIVE,
                        payload={'cmd': 'tower_accept_guild_invite', 'leader_id': leader_id})
    keyboard.add_button('❌ Отказаться', color=VkKeyboardColor.NEGATIVE,
                        payload={'cmd': 'tower_decline_invite'})
    from guild import get_guild_member_vk_ids
    members = get_guild_member_vk_ids(guild['id'])
    await send_guild_message(vk, leader_id, guild['id'],
                       f'🏰 {char["name"]} приглашает гильдию на штурм Башни!\n'
                       f'📌 ID лидера: {leader_id}\n'
                       f'🔄 Нажмите кнопку ниже, чтобы присоединиться:')
    for member_vk_id in members:
        try:
            await send_message(vk, member_vk_id,
                         f'🏰 {char["name"]} приглашает вас на штурм Башни!\n'
                         f'📌 ID лидера: {leader_id}',
                         keyboard)
        except:
            pass

async def join_tower_party(vk, leader_id, member_id):
    from guild import get_guild_by_character
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    leader_guild = get_guild_by_character(leader_id)
    if not leader_guild:
        conn.close()
        return False, "Лидер не состоит в гильдии."
    member_guild = get_guild_by_character(member_id)
    if not member_guild:
        conn.close()
        return False, "Вы не состоите в гильдии."
    if leader_guild['id'] != member_guild['id']:
        conn.close()
        return False, "Вы не в одной гильдии с лидером."
    cur.execute('SELECT id, members FROM tower_party WHERE leader_id = ? AND active = 1', (leader_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Группа не найдена или неактивна."
    party_id, members_json = row
    members = json.loads(members_json)
    if len(members) >= 5:
        conn.close()
        return False, "Группа заполнена (макс. 5)."
    if member_id in members:
        conn.close()
        return False, "Вы уже в группе."
    members.append(member_id)
    cur.execute('UPDATE tower_party SET members = ? WHERE id = ?', (json.dumps(members), party_id))
    conn.commit()
    conn.close()
    await _send_party_composition(vk, party_id)
    leader_char = get_character_by_id(leader_id)
    member_char = get_character_by_id(member_id)
    if leader_char and member_char:
        guild = get_guild_by_character(leader_id)
        if guild:
            await send_guild_message(vk, leader_id, guild['id'],
                               f'👤 {member_char["name"]} присоединился к группе Башни! Состав: {len(members)}/5')
    return True, "Вы присоединились к группе!"

async def _send_party_composition(vk, party_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT leader_id, members FROM tower_party WHERE id = ? AND active = 1', (party_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return
    leader_id, members_json = row
    members = json.loads(members_json)
    text = "👥 Состав группы:\n"
    leader = get_character_by_id(leader_id)
    text += f"👑 {leader['name']} (Лидер)\n" if leader else "👑 Лидер\n"
    for member_id in members:
        if member_id == leader_id:
            continue
        char = get_character_by_id(member_id)
        text += f"👤 {char['name']}\n" if char else "👤 Неизвестный\n"
    text += f"\n📊 Всего: {len(members)}/5"
    await send_tower_chat_message(vk, party_id, "Система", text)

def get_tower_party(character_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, leader_id, members, current_floor, active FROM tower_party WHERE active = 1 AND leader_id = ?', (character_id,))
    row = cur.fetchone()
    if row:
        conn.close()
        return {
            'id': row[0],
            'leader_id': row[1],
            'members': json.loads(row[2]),
            'current_floor': row[3],
            'active': row[4]
        }
    cur.execute('SELECT id, leader_id, members, current_floor, active FROM tower_party WHERE active = 1')
    rows = cur.fetchall()
    conn.close()
    for r in rows:
        members = json.loads(r[2])
        if character_id in members:
            return {
                'id': r[0],
                'leader_id': r[1],
                'members': members,
                'current_floor': r[3],
                'active': r[4]
            }
    return None

async def send_tower_chat_message(vk, party_id, sender_name, text):
    if vk is None or party_id == 0:
        return False
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT members FROM tower_party WHERE id = ? AND active = 1', (party_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    members = json.loads(row[0])
    for member_id in members:
        char = await get_character_by_id_async(member_id)
        if char:
            try:
                await send_message(vk, char['vk_id'], f'💬 Чат Башни [{sender_name}]: {text}')
            except Exception:
                pass
    return True

async def start_tower_battle(vk, leader_id):
    party = await asyncio.to_thread(get_tower_party, leader_id)
    if not party:
        await send_tower_chat_message(vk, 0, "Система", "❌ Группа не найдена.")
        return False, "Группа не найдена.", []
    if party['leader_id'] != leader_id:
        await send_tower_chat_message(vk, party['id'], "Система", "❌ Только лидер может начать бой.")
        return False, "Только лидер может начать бой.", []
    if party['current_floor'] > 10:
        await send_tower_chat_message(vk, party['id'], "Система", "🎉 Вы прошли все 10 этажей!")
        return False, "Вы уже прошли все этажи.", []
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for member_id in party['members']:
        cur.execute('SELECT hp FROM characters WHERE id = ?', (member_id,))
        hp = cur.fetchone()[0]
        if hp <= 0:
            conn.close()
            char = await get_character_by_id_async(member_id)
            await send_tower_chat_message(vk, party['id'], "Система", f"❌ {char['name']} мёртв! Он должен воскреснуть в соборе.")
            return False, f"Игрок {char['name']} мёртв.", []
    conn.close()
    boss = await asyncio.to_thread(get_tower_boss, party['current_floor'])
    if boss:
        boss_image = boss.get('image')
        await send_tower_chat_message(vk, party['id'], "⚔️ Бой",
            f"⚔️ {boss['name']} (Этаж {party['current_floor']})\n"
            f"❤️ HP: {boss['hp']} | ⚔️ Атака: {boss['attack']} | 🛡 Защита: {boss['defense']}"
        )
        await asyncio.sleep(2)
        if boss_image:
            for member_id in party['members']:
                char = await get_character_by_id_async(member_id)
                if char:
                    try:
                        await send_message(vk, char['vk_id'],
                            f"⚔️ Вас ждёт {boss['name']} (Этаж {party['current_floor']})",
                            attachment=boss_image
                        )
                    except Exception:
                        pass
    await send_tower_chat_message(vk, party['id'], "Система", "⚔️ Бой начинается!")
    await asyncio.sleep(1)
    success, msg, log = await process_tower_battle(vk, leader_id)
    return success, msg, log

async def process_tower_battle(vk, leader_id):
    party = await asyncio.to_thread(get_tower_party, leader_id)
    if not party:
        return False, "Группа не найдена.", []
    boss = await asyncio.to_thread(get_tower_boss, party['current_floor'])
    if not boss:
        return False, "Босс не найден.", []
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    party_stats = []
    for member_id in party['members']:
        cur.execute('SELECT name, hp, max_hp, mana, max_mana, stamina, max_stamina, attack, defense, crit_chance, dodge_chance FROM characters WHERE id = ?', (member_id,))
        stats = cur.fetchone()
        if stats:
            party_stats.append({
                'id': member_id,
                'name': stats[0],
                'hp': stats[1],
                'max_hp': stats[2],
                'mana': stats[3],
                'max_mana': stats[4],
                'stamina': stats[5],
                'max_stamina': stats[6],
                'attack': stats[7],
                'defense': stats[8],
                'crit': stats[9],
                'dodge': stats[10],
                'alive': stats[1] > 0
            })
    if not party_stats:
        conn.close()
        return False, "Нет данных о членах группы.", []
    
    total_hp = sum(p['hp'] for p in party_stats if p['alive'])
    total_max_hp = sum(p['max_hp'] for p in party_stats)
    total_attack = sum(p['attack'] for p in party_stats if p['alive'])
    total_defense = sum(p['defense'] for p in party_stats if p['alive'])
    avg_crit = sum(p['crit'] for p in party_stats if p['alive']) / max(1, len([p for p in party_stats if p['alive']]))
    avg_dodge = sum(p['dodge'] for p in party_stats if p['alive']) / max(1, len([p for p in party_stats if p['alive']]))
    boss_hp = boss['hp']
    boss_max_hp = boss['max_hp']
    boss_attack = boss['attack']
    boss_defense = boss['defense']
    log = []
    round_num = 0
    max_rounds = 20
    party_id = party['id']

    while boss_hp > 0 and total_hp > 0 and round_num < max_rounds:
        round_num += 1
        
        alive_players = [p for p in party_stats if p['alive']]
        if not alive_players:
            await send_tower_chat_message(vk, party_id, "⚔️ Бой", "💀 ВСЕ ЧЛЕНЫ ГРУППЫ ПАЛИ!")
            log.append("Группа пала")
            break
        
        group_damage = 0
        crit_triggered = False
        for p in alive_players:
            atk = p['attack']
            if random.random() * 100 < avg_crit:
                atk = int(atk * 1.5)
                crit_triggered = True
            dmg = max(1, atk - boss_defense // len(alive_players))
            group_damage += dmg
        total_damage = max(1, group_damage - boss_defense // 2)
        boss_hp -= total_damage
        if boss_hp < 0:
            boss_hp = 0
        log.append(f"Раунд {round_num}: группа наносит {total_damage} урона{' (КРИТ!)' if crit_triggered else ''}")
        await send_tower_chat_message(vk, party_id, "⚔️ Бой",
                               f"🔴 Раунд {round_num}\n⚔️ Группа наносит {total_damage} урона{' (КРИТ!)' if crit_triggered else ''}\n❤️ Босс: {boss_hp}/{boss_max_hp} HP")
        await asyncio.sleep(0.7)
        
        if boss_hp <= 0:
            break
        
        target = random.choice(alive_players)
        dodge_chance = avg_dodge
        if random.random() * 100 < dodge_chance:
            await send_tower_chat_message(vk, party_id, "⚔️ Бой", f"💨 Босс атакует {target['name']}, но тот уклоняется!")
            log.append(f"Босс атакует {target['name']}, уклонение!")
            await asyncio.sleep(0.7)
        else:
            boss_attack_power = boss_attack + random.randint(-3, 3)
            damage = max(1, boss_attack_power - target['defense'] // 2)
            target['hp'] -= damage
            if target['hp'] < 0:
                target['hp'] = 0
            
            if target['hp'] <= 0:
                target['alive'] = False
                await send_tower_chat_message(vk, party_id, "⚔️ Бой", f"💀 {target['name']} погиб!")
                log.append(f"{target['name']} погиб")
            
            total_hp = sum(p['hp'] for p in party_stats if p['alive'])
            
            await send_tower_chat_message(vk, party_id, "⚔️ Бой",
                                   f"💢 Босс атакует {target['name']} на {damage} урона\n❤️ {target['name']}: {target['hp']}/{target['max_hp']} HP")
            log.append(f"Босс нанёс {damage} урона {target['name']}")
            await asyncio.sleep(0.7)
        
        if total_hp <= 0:
            await send_tower_chat_message(vk, party_id, "⚔️ Бой", "💀 ВСЕ ЧЛЕНЫ ГРУППЫ ПАЛИ!")
            log.append("Группа пала")
            break

    # Обновляем HP в базе данных
    for p in party_stats:
        cur.execute('UPDATE characters SET hp = ? WHERE id = ?', (p['hp'], p['id']))

    if boss_hp <= 0:
        # ... (код победы без изменений)
        exp_gain = boss['exp']
        silver_gain = boss['silver']
        for member_id in party['members']:
            cur.execute('UPDATE characters SET exp = exp + ?, silver = silver + ? WHERE id = ?', (exp_gain, silver_gain, member_id))
            cur.execute('SELECT level, exp, max_hp, hp, attack, defense, max_mana, mana, max_stamina, stamina FROM characters WHERE id = ?', (member_id,))
            row = cur.fetchone()
            if row:
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
                                (level, exp, max_hp, hp, attack, defense, max_mana, mana, max_stamina, stamina, member_id))
        new_floor = party['current_floor'] + 1
        cur.execute('UPDATE tower_party SET current_floor = ? WHERE id = ?', (new_floor, party['id']))
        conn.commit()
        conn.close()
        for member_id in party['members']:
            await recalc_stats_async(member_id)
        
        for member_id in party['members']:
            char = await get_character_by_id_async(member_id)
            if char:
                await send_message(vk, char['vk_id'],
                             f"⚔️ Победа над {boss['name']}!\n\n" + "\n".join(log[-10:]) +
                             f"\n\n✨ Все получили {exp_gain} опыта и {silver_gain} серебра\n⬆️ Переход на этаж {new_floor}")
        
        await send_tower_chat_message(vk, party_id, "⚔️ Бой",
                               f"🎉 ПОБЕДА!\n✨ Все получили {exp_gain} опыта и {silver_gain} серебра\n⬆️ Переход на этаж {new_floor}")
        return True, "Победа!", log
    else:
        # ===== ПОРАЖЕНИЕ =====
        # Накладываем дебафф на всех
        for member_id in party['members']:
            cur.execute('UPDATE characters SET debuff = 2 WHERE id = ?', (member_id,))
            cur.execute('UPDATE characters SET hp = max_hp / 2, mana = max_mana / 2, stamina = max_stamina / 2 WHERE id = ?', (member_id,))
        cur.execute('UPDATE tower_party SET active = 0 WHERE id = ?', (party['id'],))
        conn.commit()
        conn.close()
        
        # Пересчет статов для всех
        for member_id in party['members']:
            await recalc_stats_async(member_id)
        
        # Отправляем сообщение о поражении и перенаправляем КАЖДОГО в Собор
        from locations import show_church
        
        for member_id in party['members']:
            char = await get_character_by_id_async(member_id)
            if char:
                # Отправляем сообщение
                await send_message(vk, char['vk_id'],
                             f"💀 Поражение от {boss['name']}...\n\n" + "\n".join(log[-10:]) +
                             "\n\nГруппа разбита. Вы получили Печать башни (-50% к статам).\n\n🏛️ Вы направлены в Собор для снятия проклятия.")
                
                # Обновляем состояние
                await update_user_async(char['vk_id'], state='church', context={'parent_state': 'meadow'})
                
                # ОТКРЫВАЕМ СОБОР ДЛЯ КАЖДОГО
                await show_church(vk, char['vk_id'])
        
        await send_tower_chat_message(vk, party_id, "⚔️ Бой",
                               "💀 ПОРАЖЕНИЕ!\nГруппа разбита. Все получили Печать башни (-50% к статам).")
        
        return False, "Поражение! Вы направлены в Собор.", log

async def rest_in_tower(character_id):
    party = await asyncio.to_thread(get_tower_party, character_id)
    if not party:
        return False, "Вы не в группе."
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for member_id in party['members']:
        cur.execute('UPDATE characters SET hp = max_hp, mana = max_mana, stamina = max_stamina WHERE id = ?', (member_id,))
    conn.commit()
    conn.close()
    await send_tower_chat_message(None, party['id'], "Система", "🔄 Все восстановлены!")
    return True, "Все восстановлены!"

async def leave_tower(character_id):
    party = await asyncio.to_thread(get_tower_party, character_id)
    if not party:
        return False, "Вы не в группе."
    is_leader = party['leader_id'] == character_id
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if is_leader:
        await send_tower_chat_message(None, party['id'], "Система", "👑 Лидер покинул группу. Группа расформирована.")
        cur.execute('UPDATE tower_party SET active = 0 WHERE id = ?', (party['id'],))
        conn.commit()
        conn.close()
        return True, "Вы вышли из башни. Группа расформирована."
    else:
        members = party['members']
        members.remove(character_id)
        cur.execute('UPDATE tower_party SET members = ? WHERE id = ?', (json.dumps(members), party['id']))
        conn.commit()
        conn.close()
        char = await get_character_by_id_async(character_id)
        await send_tower_chat_message(None, party['id'], "Система", f"👤 {char['name']} покинул группу. Состав: {len(members)}/5")
        return True, "Вы покинули группу."

async def handle_tower_accept_guild_invite(vk, user_id, leader_id):
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.')
        return
    existing_party = await asyncio.to_thread(get_tower_party, char['id'])
    if existing_party:
        await send_message(vk, user_id, 'Вы уже состоите в группе!')
        from locations import show_tower
        await show_tower(vk, user_id)
        return
    success, msg = await join_tower_party(vk, leader_id, char['id'])
    await send_message(vk, user_id, msg)
    if success:
        await update_user_async(user_id, state='tower', context={'parent_state': 'meadow'})
        await asyncio.sleep(0.3)
        from locations import show_tower
        await show_tower(vk, user_id)
    else:
        from locations import show_tower
        await show_tower(vk, user_id)

async def handle_tower_accept_invite(vk, user_id, leader_id):
    """Обработчик принятия личного приглашения в группу"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.')
        return
    
    existing_party = await asyncio.to_thread(get_tower_party, char['id'])
    if existing_party:
        await send_message(vk, user_id, 'Вы уже состоите в группе!')
        return
    
    success, msg = await join_tower_party(vk, leader_id, char['id'])
    await send_message(vk, user_id, msg)
    if success:
        await update_user_async(user_id, state='tower', context={'parent_state': 'meadow'})
        await asyncio.sleep(0.3)
        from locations import show_tower
        await show_tower(vk, user_id)

async def handle_tower_decline_invite(vk, user_id, leader_id=None):
    """Обработчик отказа от приглашения"""
    await send_message(vk, user_id, '❌ Вы отказались от приглашения.')