# guild.py
import sqlite3
import json
import asyncio
from config import DB_NAME
from core import get_character_by_id, send_message, get_character_by_id_async
from items import get_item_stats

def create_guild(leader_id, name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT guild_id FROM guild_members WHERE character_id = ?', (leader_id,))
    if cur.fetchone():
        conn.close()
        return None, "Вы уже состоите в гильдии."
    cur.execute('INSERT INTO guilds (name, leader_id, max_members) VALUES (?, ?, 10)', (name, leader_id))
    guild_id = cur.lastrowid
    cur.execute('INSERT INTO guild_members (guild_id, character_id, rank) VALUES (?, ?, ?)',
                (guild_id, leader_id, 'Лидер'))
    conn.commit()
    conn.close()
    return guild_id, f"Гильдия «{name}» создана!"


def join_guild(character_id, guild_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT guild_id FROM guild_members WHERE character_id = ?', (character_id,))
    if cur.fetchone():
        conn.close()
        return False, "Вы уже состоите в гильдии."
    cur.execute('SELECT id, max_members FROM guilds WHERE id = ?', (guild_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Гильдия не найдена."
    cur.execute('SELECT COUNT(*) FROM guild_members WHERE guild_id = ?', (guild_id,))
    count = cur.fetchone()[0]
    if count >= row[1]:
        conn.close()
        return False, "Гильдия заполнена."
    cur.execute('INSERT INTO guild_members (guild_id, character_id) VALUES (?, ?)', (guild_id, character_id))
    conn.commit()
    conn.close()
    return True, "Вы вступили в гильдию!"


def leave_guild(character_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT guild_id, rank FROM guild_members WHERE character_id = ?', (character_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Вы не состоите в гильдии."
    guild_id, rank = row
    if rank == 'Лидер':
        cur.execute('DELETE FROM guild_members WHERE guild_id = ?', (guild_id,))
        cur.execute('DELETE FROM guild_storage WHERE guild_id = ?', (guild_id,))
        cur.execute('DELETE FROM guilds WHERE id = ?', (guild_id,))
        conn.commit()
        conn.close()
        return True, "Гильдия расформирована."
    else:
        cur.execute('DELETE FROM guild_members WHERE character_id = ?', (character_id,))
        conn.commit()
        conn.close()
        return True, "Вы покинули гильдию."


def get_guild(guild_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, name, leader_id, level, exp, silver, max_members FROM guilds WHERE id = ?', (guild_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'leader_id': row[2],
            'level': row[3],
            'exp': row[4],
            'silver': row[5],
            'max_members': row[6]
        }
    return None


def get_guild_by_character(character_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT g.id, g.name, g.leader_id, g.level, g.exp, g.silver, g.max_members
        FROM guilds g JOIN guild_members gm ON g.id = gm.guild_id
        WHERE gm.character_id = ?
    ''', (character_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'leader_id': row[2],
            'level': row[3],
            'exp': row[4],
            'silver': row[5],
            'max_members': row[6]
        }
    return None


def get_guild_members(guild_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT c.id, c.name, gm.rank
        FROM guild_members gm JOIN characters c ON gm.character_id = c.id
        WHERE gm.guild_id = ?
        ORDER BY gm.rank DESC, gm.joined_at ASC
    ''', (guild_id,))
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'rank': r[2]} for r in rows]


def get_all_guilds(limit=20):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, name, level, silver FROM guilds ORDER BY level DESC, silver DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'level': r[2], 'silver': r[3]} for r in rows]


def set_rank(character_id, target_id, new_rank):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''SELECT gm1.guild_id, gm1.rank, gm2.rank
                   FROM guild_members gm1 JOIN guild_members gm2 ON gm1.guild_id = gm2.guild_id
                   WHERE gm1.character_id = ? AND gm2.character_id = ?''', (character_id, target_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Вы не в одной гильдии."
    guild_id, my_rank, target_rank = row
    if my_rank not in ('Лидер', 'Заместитель'):
        conn.close()
        return False, "Нет прав."
    if my_rank == 'Заместитель' and new_rank in ('Лидер', 'Заместитель'):
        conn.close()
        return False, "Заместитель не может назначать лидера или заместителя."
    if target_rank == 'Лидер':
        conn.close()
        return False, "Нельзя изменить ранг лидера."
    cur.execute('UPDATE guild_members SET rank = ? WHERE guild_id = ? AND character_id = ?', (new_rank, guild_id, target_id))
    conn.commit()
    conn.close()
    return True, f"Ранг изменён на {new_rank}."


def kick_member(character_id, target_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''SELECT gm1.guild_id, gm1.rank, gm2.rank
                   FROM guild_members gm1 JOIN guild_members gm2 ON gm1.guild_id = gm2.guild_id
                   WHERE gm1.character_id = ? AND gm2.character_id = ?''', (character_id, target_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Вы не в одной гильдии."
    guild_id, my_rank, target_rank = row
    if my_rank not in ('Лидер', 'Заместитель'):
        conn.close()
        return False, "Нет прав."
    if target_rank == 'Лидер':
        conn.close()
        return False, "Нельзя исключить лидера."
    if target_rank == 'Заместитель' and my_rank == 'Заместитель':
        conn.close()
        return False, "Заместитель не может исключить другого заместителя."
    cur.execute('DELETE FROM guild_members WHERE guild_id = ? AND character_id = ?', (guild_id, target_id))
    conn.commit()
    conn.close()
    return True, "Участник исключён."


def get_guild_member_vk_ids(guild_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT c.vk_id FROM guild_members gm JOIN characters c ON gm.character_id = c.id
        WHERE gm.guild_id = ?
    ''', (guild_id,))
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


async def send_guild_message(vk, character_id, guild_id, text):
    char = await get_character_by_id_async(character_id)
    if not char:
        return False, "Персонаж не найден."
    members = get_guild_member_vk_ids(guild_id)
    if not members:
        return False, "Нет участников."
    for vk_id in members:
        await send_message(vk, vk_id, f"💬 Чат гильдии [{char['name']}]: {text}")
    return True, "Сообщение отправлено."


def guild_exp_to_next_level(level):
    return 1000 + 2500 * (level - 1) if level > 1 else 1000


def add_guild_exp(guild_id, exp):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT level, exp FROM guilds WHERE id = ?', (guild_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return
    level, current_exp = row
    current_exp += exp
    while True:
        needed = guild_exp_to_next_level(level)
        if current_exp >= needed:
            current_exp -= needed
            level += 1
            cur.execute('UPDATE guilds SET max_members = max_members + 3 WHERE id = ?', (guild_id,))
        else:
            break
    cur.execute('UPDATE guilds SET level = ?, exp = ? WHERE id = ?', (level, current_exp, guild_id))
    conn.commit()
    conn.close()
    return level


def get_guild_storage(guild_id):
    """Получение всех предметов на складе гильдии"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, template_id, level, rarity, upgrade_level, quantity, item_type, name FROM guild_storage WHERE guild_id = ?', (guild_id,))
    rows = cur.fetchall()
    conn.close()
    items = []
    for row in rows:
        item = {
            'id': row[0],
            'template_id': row[1],
            'level': row[2],
            'rarity': row[3],
            'upgrade_level': row[4],
            'quantity': row[5],
            'item_type': row[6] or 'item',
            'name': row[7] or 'Неизвестный предмет'
        }
        if item['item_type'] == 'item':
            stats = get_item_stats(row[1], row[2], row[3], row[4])
            if stats:
                item.update(stats)
        items.append(item)
    return items


def add_to_guild_storage(character_id, item_id, item_type='item'):
    """Добавление предмета на склад гильдии"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    guild = get_guild_by_character(character_id)
    if not guild:
        conn.close()
        return False, "Вы не состоите в гильдии."
    
    guild_id = guild['id']
    
    if item_type == 'item':
        cur.execute('SELECT owner_id, template_id, level, rarity, upgrade_level, quantity FROM player_items WHERE id = ?', (item_id,))
        row = cur.fetchone()
        if not row or row[0] != character_id:
            conn.close()
            return False, "Предмет не найден или не принадлежит вам."
        
        template_id, level, rarity, upgrade_level, quantity = row[1], row[2], row[3], row[4], row[5]
        
        stats = get_item_stats(template_id, level, rarity, upgrade_level)
        name = stats['name'] if stats else 'Неизвестный предмет'
        
        cur.execute('DELETE FROM player_items WHERE id = ?', (item_id,))
        cur.execute('''
            INSERT INTO guild_storage (guild_id, template_id, level, rarity, upgrade_level, quantity, item_type, name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (guild_id, template_id, level, rarity, upgrade_level, quantity, 'item', name))
        
    elif item_type == 'crystal':
        from core import get_player_crystals
        cur.execute('SELECT id, consumable_template_id, quantity FROM player_consumables WHERE id = ? AND owner_id = ?', (item_id, character_id))
        row = cur.fetchone()
        if not row:
            conn.close()
            return False, "Кристалл не найден или не принадлежит вам."
        
        consumable_id, template_id, quantity = row
        
        cur.execute('SELECT name FROM consumable_templates WHERE id = ?', (template_id,))
        name_row = cur.fetchone()
        name = name_row[0] if name_row else 'Кристалл'
        
        cur.execute('DELETE FROM player_consumables WHERE id = ?', (consumable_id,))
        cur.execute('''
            INSERT INTO guild_storage (guild_id, template_id, level, rarity, upgrade_level, quantity, item_type, name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (guild_id, template_id, 1, 1, 0, quantity, 'crystal', name))
    
    else:
        conn.close()
        return False, "Неизвестный тип предмета."
    
    conn.commit()
    conn.close()
    return True, f"Предмет добавлен на склад гильдии (x{quantity})."


def remove_from_guild_storage(guild_id, storage_id, quantity, character_id):
    """Изъятие предмета со склада гильдии"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute('SELECT template_id, level, rarity, upgrade_level, quantity, item_type, name FROM guild_storage WHERE id = ? AND guild_id = ?', (storage_id, guild_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Предмет не найден на складе."
    
    template_id, level, rarity, upgrade_level, qty, item_type, name = row
    
    if qty < quantity:
        conn.close()
        return False, f"На складе только {qty} шт."
    
    if item_type == 'item':
        cur.execute('INSERT INTO player_items (owner_id, template_id, level, rarity, upgrade_level, quantity) VALUES (?, ?, ?, ?, ?, ?)',
                    (character_id, template_id, level, rarity, upgrade_level, quantity))
    elif item_type == 'crystal':
        cur.execute('INSERT INTO player_consumables (owner_id, consumable_template_id, quantity) VALUES (?, ?, ?)',
                    (character_id, template_id, quantity))
    else:
        conn.close()
        return False, "Неизвестный тип предмета."
    
    if qty == quantity:
        cur.execute('DELETE FROM guild_storage WHERE id = ?', (storage_id,))
    else:
        cur.execute('UPDATE guild_storage SET quantity = quantity - ? WHERE id = ?', (quantity, storage_id))
    
    conn.commit()
    conn.close()
    return True, f"Вы забрали {quantity} шт. со склада ({name})."


# ===== НОВЫЕ ФУНКЦИИ ДЛЯ СИСТЕМЫ ЗАЯВОК =====

def get_guilds_list(page=1, per_page=5):
    """Получение списка гильдий с пагинацией"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM guilds')
    total = cur.fetchone()[0]
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    offset = (page - 1) * per_page
    cur.execute('''
        SELECT g.id, g.name, g.level, g.silver, g.max_members,
               (SELECT COUNT(*) FROM guild_members WHERE guild_id = g.id) as members_count
        FROM guilds g
        ORDER BY g.level DESC, g.silver DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    rows = cur.fetchall()
    conn.close()
    
    guilds = []
    for row in rows:
        guilds.append({
            'id': row[0],
            'name': row[1],
            'level': row[2],
            'silver': row[3],
            'max_members': row[4],
            'members': row[5]
        })
    
    return guilds, total_pages


def get_guild_applications(guild_id, status='pending'):
    """Получение заявок в гильдию"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT ga.id, ga.player_id, c.name, c.level, c.class, ga.created_at
        FROM guild_applications ga
        JOIN characters c ON ga.player_id = c.id
        WHERE ga.guild_id = ? AND ga.status = ?
        ORDER BY ga.created_at ASC
    ''', (guild_id, status))
    rows = cur.fetchall()
    conn.close()
    
    apps = []
    for row in rows:
        apps.append({
            'id': row[0],
            'player_id': row[1],
            'name': row[2],
            'level': row[3],
            'class': row[4] or 'Не выбран',
            'created_at': row[5]
        })
    return apps


def apply_to_guild(player_id, guild_id):
    """Подача заявки в гильдию"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute('SELECT guild_id FROM guild_members WHERE character_id = ?', (player_id,))
    if cur.fetchone():
        conn.close()
        return False, "Вы уже состоите в гильдии."
    
    cur.execute('SELECT id FROM guild_applications WHERE player_id = ? AND guild_id = ? AND status = "pending"',
                (player_id, guild_id))
    if cur.fetchone():
        conn.close()
        return False, "Вы уже подали заявку в эту гильдию."
    
    cur.execute('''
        INSERT INTO guild_applications (guild_id, player_id, status)
        VALUES (?, ?, 'pending')
    ''', (guild_id, player_id))
    conn.commit()
    conn.close()
    return True, "Заявка подана!"


def accept_application(application_id, reviewer_id):
    """Принятие заявки"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute('SELECT guild_id, player_id FROM guild_applications WHERE id = ? AND status = "pending"',
                (application_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Заявка не найдена или уже обработана."
    
    guild_id, player_id = row
    
    cur.execute('SELECT max_members FROM guilds WHERE id = ?', (guild_id,))
    max_members = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM guild_members WHERE guild_id = ?', (guild_id,))
    count = cur.fetchone()[0]
    if count >= max_members:
        conn.close()
        return False, "Гильдия заполнена."
    
    cur.execute('INSERT INTO guild_members (guild_id, character_id, rank) VALUES (?, ?, ?)',
                (guild_id, player_id, 'Участник'))
    
    cur.execute('''
        UPDATE guild_applications 
        SET status = 'accepted', reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ?
        WHERE id = ?
    ''', (reviewer_id, application_id))
    
    conn.commit()
    conn.close()
    return True, "Игрок принят в гильдию!"


def reject_application(application_id, reviewer_id):
    """Отклонение заявки"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute('''
        UPDATE guild_applications 
        SET status = 'rejected', reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ?
        WHERE id = ? AND status = 'pending'
    ''', (reviewer_id, application_id))
    
    if cur.rowcount == 0:
        conn.close()
        return False, "Заявка не найдена или уже обработана."
    
    conn.commit()
    conn.close()
    return True, "Заявка отклонена."


def get_guild_rank(character_id, guild_id):
    """Получение ранга игрока в гильдии"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT rank FROM guild_members WHERE guild_id = ? AND character_id = ?',
                (guild_id, character_id))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_guild_applications_count(guild_id):
    """Получение количества новых заявок"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM guild_applications WHERE guild_id = ? AND status = "pending"',
                (guild_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count