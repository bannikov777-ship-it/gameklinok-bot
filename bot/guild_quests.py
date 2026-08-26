# guild_quests.py (полный исправленный)
import sqlite3
import json
import asyncio
import datetime
import random
import traceback
from config import DB_NAME
from core import get_character_by_id, send_message, get_user_async, get_character_async, update_user_async
from scheduler import scheduler
from guild import get_guild_by_character, add_guild_exp


# ========== ЕЖЕДНЕВНЫЕ КВЕСТЫ ГИЛЬДИИ ==========

def get_daily_guild_quests(guild_id):
    """Получение ежедневных квестов для гильдии"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Проверяем, есть ли уже квесты на сегодня
    cur.execute('SELECT quests FROM guild_quests_daily WHERE guild_id = ? AND date = ?', (guild_id, today))
    row = cur.fetchone()
    
    if row:
        quest_ids = json.loads(row[0])
        conn.close()
        return get_quests_by_ids(quest_ids)
    
    # Генерируем новые квесты
    all_quests = get_all_quest_templates()
    random.shuffle(all_quests)
    
    # Выбираем 3 квеста
    selected = all_quests[:3]
    quest_ids = [q['id'] for q in selected]
    
    cur.execute('''
        INSERT INTO guild_quests_daily (guild_id, date, quests)
        VALUES (?, ?, ?)
    ''', (guild_id, today, json.dumps(quest_ids)))
    conn.commit()
    conn.close()
    
    return selected


def get_all_quest_templates():
    """Получение всех шаблонов квестов"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, name, description, duration_minutes, exp_reward, silver_reward, '
                'extra_reward_type, extra_reward_id, extra_reward_quantity, extra_reward_rarity '
                'FROM guild_quests')
    rows = cur.fetchall()
    conn.close()
    
    quests = []
    for row in rows:
        quests.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'duration_minutes': row[3],
            'exp_reward': row[4],
            'silver_reward': row[5],
            'extra_reward_type': row[6],
            'extra_reward_id': row[7],
            'extra_reward_quantity': row[8] or 1,
            'extra_reward_rarity': row[9] or 1
        })
    return quests


def get_quests_by_ids(quest_ids):
    """Получение квестов по ID"""
    if not quest_ids:
        return []
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    placeholders = ','.join('?' for _ in quest_ids)
    cur.execute(f'''
        SELECT id, name, description, duration_minutes, exp_reward, silver_reward,
               extra_reward_type, extra_reward_id, extra_reward_quantity, extra_reward_rarity
        FROM guild_quests WHERE id IN ({placeholders})
    ''', quest_ids)
    rows = cur.fetchall()
    conn.close()
    
    quests = []
    for row in rows:
        quests.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'duration_minutes': row[3],
            'exp_reward': row[4],
            'silver_reward': row[5],
            'extra_reward_type': row[6],
            'extra_reward_id': row[7],
            'extra_reward_quantity': row[8] or 1,
            'extra_reward_rarity': row[9] or 1
        })
    return quests


def get_available_guild_quests(player_id):
    """Получение доступных квестов для игрока (ежедневные)"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Получаем гильдию игрока
    cur.execute('SELECT guild_id FROM guild_members WHERE character_id = ?', (player_id,))
    guild_row = cur.fetchone()
    if not guild_row:
        conn.close()
        return []
    
    guild_id = guild_row[0]
    
    # Получаем ежедневные квесты гильдии
    daily_quests = get_daily_guild_quests(guild_id)
    daily_ids = [q['id'] for q in daily_quests]
    
    # Получаем уже взятые игроком квесты
    cur.execute('SELECT quest_id FROM player_guild_quests WHERE player_id = ?', (player_id,))
    taken = [row[0] for row in cur.fetchall()]
    conn.close()
    
    # Возвращаем только те, которые ещё не взяты
    available = [q for q in daily_quests if q['id'] not in taken]
    
    return available


def get_quest_by_id(quest_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, name, description, duration_minutes, exp_reward, silver_reward, '
                'extra_reward_type, extra_reward_id, extra_reward_quantity, extra_reward_rarity '
                'FROM guild_quests WHERE id = ?', (quest_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'duration_minutes': row[3],
            'exp_reward': row[4],
            'silver_reward': row[5],
            'extra_reward_type': row[6],
            'extra_reward_id': row[7],
            'extra_reward_quantity': row[8] or 1,
            'extra_reward_rarity': row[9] or 1
        }
    return None


async def take_guild_quest(vk, user_id, quest_id):
    print(f"📌 take_guild_quest: user_id={user_id}, quest_id={quest_id}")
    char = await get_character_async(user_id)
    if not char:
        return False, "Сначала создайте персонажа."

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM player_guild_quests WHERE player_id = ? AND completed = 0', (char['id'],))
    if cur.fetchone():
        conn.close()
        return False, "У вас уже есть активный гильдейский квест! Завершите его."

    cur.execute('SELECT id FROM player_guild_quests WHERE player_id = ? AND quest_id = ?', (char['id'], quest_id))
    if cur.fetchone():
        conn.close()
        return False, "Вы уже брали этот квест ранее."

    quest = get_quest_by_id(quest_id)
    if not quest:
        conn.close()
        return False, "Квест не найден."

    cur.execute('''
        INSERT INTO player_guild_quests (player_id, quest_id, start_time, end_time)
        VALUES (?, ?, datetime('now'), datetime('now', '+' || ? || ' minutes'))
    ''', (char['id'], quest_id, quest['duration_minutes']))
    conn.commit()
    conn.close()

    delay_seconds = quest['duration_minutes'] * 60
    task_id = scheduler.schedule(delay_seconds, complete_guild_quest, vk, user_id, quest_id)
    print(f"⏳ Планируем квест '{quest['name']}' через {delay_seconds} сек для пользователя {user_id}")
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['guild_quest_task_id'] = task_id
    await update_user_async(user_id, context=context)

    return True, f"✅ Квест '{quest['name']}' взят! Он будет выполнен через {quest['duration_minutes']} минут."


async def complete_guild_quest(vk, user_id, quest_id):
    print(f"🔥🔥🔥 complete_guild_quest ВЫЗВАНА для user_id={user_id}, quest_id={quest_id}")
    conn = None
    try:
        char = await get_character_async(user_id)
        if not char:
            print("❌ Персонаж не найден")
            return
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('SELECT id, completed, rewarded FROM player_guild_quests WHERE player_id = ? AND quest_id = ? AND completed = 0', (char['id'], quest_id))
        row = cur.fetchone()
        if not row:
            print("❌ Квест не найден или уже выполнен")
            return
        player_quest_id = row[0]
        if row[2] == 1:
            print("❌ Квест уже награждён")
            return

        quest = get_quest_by_id(quest_id)
        if not quest:
            print("❌ Шаблон квеста не найден")
            return

        cur.execute('UPDATE player_guild_quests SET completed = 1, rewarded = 1 WHERE id = ?', (player_quest_id,))
        cur.execute('UPDATE characters SET exp = exp + ?, silver = silver + ? WHERE id = ?', 
                    (quest['exp_reward'], quest['silver_reward'], char['id']))
        cur.execute('UPDATE characters SET guild_exp_contributed = guild_exp_contributed + ? WHERE id = ?', 
                    (quest['exp_reward'], char['id']))
        cur.execute('UPDATE characters SET guild_quests_completed = guild_quests_completed + 1 WHERE id = ?', 
                    (char['id'],))

        conn.commit()

        guild = get_guild_by_character(char['id'])
        if guild:
            add_guild_exp(guild['id'], quest['exp_reward'])

        extra_text = ""
        if quest['extra_reward_type']:
            extra_text = await give_extra_reward(conn, cur, char['id'], quest)
            if extra_text:
                extra_text = f"\n+ {extra_text}"

        conn.commit()
        conn.close()
        conn = None

        user_data = await get_user_async(user_id)
        context = user_data['context']
        if 'guild_quest_task_id' in context:
            del context['guild_quest_task_id']
        await update_user_async(user_id, context=context)

        await send_message(vk, user_id,
            f"✅ Квест '{quest['name']}' выполнен!\n"
            f"Получено: {quest['exp_reward']} опыта, {quest['silver_reward']} серебра{extra_text}")
        print(f"✅ Квест {quest['name']} завершён для пользователя {user_id}")
    except Exception as e:
        print(f"❌❌❌ ОШИБКА в complete_guild_quest:")
        traceback.print_exc()
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


async def give_extra_reward(conn, cur, player_id, quest):
    reward_type = quest['extra_reward_type']
    reward_id = quest['extra_reward_id']
    quantity = quest['extra_reward_quantity']
    rarity = quest['extra_reward_rarity']

    if reward_type == 'consumable':
        cur.execute('INSERT INTO player_consumables (owner_id, consumable_template_id, quantity) VALUES (?, ?, ?) '
                    'ON CONFLICT(owner_id, consumable_template_id) DO UPDATE SET quantity = quantity + ?',
                    (player_id, reward_id, quantity, quantity))
        return f"Зелье x{quantity}"
    elif reward_type == 'herb':
        if not reward_id:
            herb_ids = [1,2,3,4,5,6,7,8]
            reward_id = random.choice(herb_ids)
        cur.execute('INSERT INTO player_herbs (owner_id, herb_id, quantity) VALUES (?, ?, ?) '
                    'ON CONFLICT(owner_id, herb_id) DO UPDATE SET quantity = quantity + ?',
                    (player_id, reward_id, quantity, quantity))
        return f"Травы x{quantity}"
    elif reward_type == 'crystal':
        cur.execute('SELECT id FROM consumable_templates WHERE restore_type = "crystal" ORDER BY RANDOM() LIMIT 1')
        crystal_id = cur.fetchone()[0]
        cur.execute('INSERT INTO player_consumables (owner_id, consumable_template_id, quantity) VALUES (?, ?, ?) '
                    'ON CONFLICT(owner_id, consumable_template_id) DO UPDATE SET quantity = quantity + ?',
                    (player_id, crystal_id, quantity, quantity))
        return f"Кристалл x{quantity}"
    elif reward_type == 'equipment' or reward_type == 'item':
        cur.execute('SELECT id FROM item_templates ORDER BY RANDOM() LIMIT 1')
        item_template_id = cur.fetchone()[0]
        cur.execute('SELECT level FROM characters WHERE id = ?', (player_id,))
        player_level = cur.fetchone()[0]
        item_level = max(1, player_level // 2)
        cur.execute('INSERT INTO player_items (owner_id, template_id, level, rarity, quantity) VALUES (?, ?, ?, ?, ?)',
                    (player_id, item_template_id, item_level, rarity, quantity))
        return f"Предмет x{quantity} (редкость {rarity}⭐)"
    else:
        return ""


async def cancel_guild_quest(vk, user_id):
    char = await get_character_async(user_id)
    if not char:
        return False, "Сначала создайте персонажа."

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, quest_id FROM player_guild_quests WHERE player_id = ? AND completed = 0', (char['id'],))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "У вас нет активного квеста."

    player_quest_id, quest_id = row
    cur.execute('DELETE FROM player_guild_quests WHERE id = ?', (player_quest_id,))
    conn.commit()
    conn.close()

    user_data = await get_user_async(user_id)
    context = user_data['context']
    if 'guild_quest_task_id' in context:
        scheduler.cancel(context['guild_quest_task_id'])
        del context['guild_quest_task_id']
    await update_user_async(user_id, context=context)

    return True, "❌ Квест отменён."


async def get_active_guild_quest(user_id):
    char = await get_character_async(user_id)
    if not char:
        return None
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''SELECT q.id, q.name, q.description, q.duration_minutes, q.exp_reward, q.silver_reward,
                          q.extra_reward_type, q.extra_reward_id, q.extra_reward_quantity, q.extra_reward_rarity,
                          p.start_time, p.end_time
                   FROM player_guild_quests p
                   JOIN guild_quests q ON p.quest_id = q.id
                   WHERE p.player_id = ? AND p.completed = 0''', (char['id'],))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'duration_minutes': row[3],
            'exp_reward': row[4],
            'silver_reward': row[5],
            'extra_reward_type': row[6],
            'extra_reward_id': row[7],
            'extra_reward_quantity': row[8] or 1,
            'extra_reward_rarity': row[9] or 1,
            'start_time': row[10],
            'end_time': row[11]
        }
    return None


async def refresh_guild_quests(vk, user_id):
    """Принудительное обновление квестов гильдии (для теста)"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, '❌ Сначала создайте персонажа.')
        return
    
    guild = get_guild_by_character(char['id'])
    if not guild:
        await send_message(vk, user_id, '❌ Вы не состоите в гильдии.')
        return
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('DELETE FROM guild_quests_daily WHERE guild_id = ?', (guild['id'],))
    conn.commit()
    conn.close()
    
    await send_message(vk, user_id, '🔄 Квесты гильдии обновлены!')