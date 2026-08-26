# core/character.py
import sqlite3
import json
from config import DB_NAME
from .stats import recalc_stats, NEUTRAL_STATS

def get_character(vk_id):
    """Получение персонажа по vk_id"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''SELECT id, name, gender, class, level, exp, silver, crystals, attack, defense, hp, max_hp, mana, max_mana,
                          stamina, max_stamina, crit_chance, dodge_chance, debuff, max_forest_depth, current_city, trophies, materials,
                          guild_exp_contributed, guild_quests_completed
                   FROM characters WHERE vk_id = ?''', (vk_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0], 'name': row[1], 'gender': row[2], 'class': row[3],
            'level': row[4], 'exp': row[5], 'silver': row[6], 'crystals': row[7],
            'attack': row[8], 'defense': row[9], 'hp': row[10], 'max_hp': row[11],
            'mana': row[12], 'max_mana': row[13], 'stamina': row[14], 'max_stamina': row[15],
            'crit_chance': row[16], 'dodge_chance': row[17], 'debuff': row[18],
            'max_forest_depth': row[19], 'current_city': row[20], 'trophies': row[21],
            'materials': json.loads(row[22]) if row[22] else {},
            'guild_exp_contributed': row[23] or 0, 'guild_quests_completed': row[24] or 0
        }
    return None

def get_character_by_id(character_id):
    """Получение персонажа по ID"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''SELECT id, vk_id, name, gender, class, level, exp, silver, crystals, attack, defense, hp, max_hp, mana, max_mana,
                          stamina, max_stamina, crit_chance, dodge_chance, debuff, max_forest_depth, current_city, trophies, materials,
                          guild_exp_contributed, guild_quests_completed
                   FROM characters WHERE id = ?''', (character_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0], 'vk_id': row[1], 'name': row[2], 'gender': row[3],
            'class': row[4], 'level': row[5], 'exp': row[6], 'silver': row[7],
            'crystals': row[8], 'attack': row[9], 'defense': row[10], 'hp': row[11],
            'max_hp': row[12], 'mana': row[13], 'max_mana': row[14], 'stamina': row[15],
            'max_stamina': row[16], 'crit_chance': row[17], 'dodge_chance': row[18],
            'debuff': row[19], 'max_forest_depth': row[20], 'current_city': row[21],
            'trophies': row[22], 'materials': json.loads(row[23]) if row[23] else {},
            'guild_exp_contributed': row[24] or 0, 'guild_quests_completed': row[25] or 0
        }
    return None

def create_character(vk_id, name, gender):
    """Создание персонажа"""
    neutral = NEUTRAL_STATS
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''INSERT OR REPLACE INTO characters
                   (vk_id, name, gender, class, level, exp, silver, crystals, attack, defense, hp, max_hp, mana, max_mana,
                    stamina, max_stamina, crit_chance, dodge_chance, debuff, max_forest_depth, current_city, trophies, materials,
                    guild_exp_contributed, guild_quests_completed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (vk_id, name, gender, None, 1, 0, 50, 0,
                 neutral['attack'], neutral['defense'], neutral['hp'], neutral['hp'],
                 neutral['mana'], neutral['mana'], neutral['stamina'], neutral['stamina'],
                 neutral['crit'], neutral['dodge'], 0, 0, 1, 0, '{}', 0, 0))
    conn.commit()
    conn.close()

def get_city(city_id):
    """Получение города по ID"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, name, description, image_attachment FROM cities WHERE id = ?', (city_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'name': row[1], 'description': row[2], 'image_attachment': row[3]}
    return None

def apply_debuff(character_id, level=1):
    """Применение дебаффа"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE characters SET debuff = ? WHERE id = ?', (level, character_id))
    conn.commit()
    conn.close()
    recalc_stats(character_id)

def remove_debuff(character_id):
    """Снятие дебаффа"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE characters SET debuff = 0 WHERE id = ?', (character_id,))
    conn.commit()
    conn.close()
    recalc_stats(character_id)

def update_max_forest_depth(character_id, depth):
    """Обновление максимальной глубины леса"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE characters SET max_forest_depth = MAX(max_forest_depth, ?) WHERE id = ?', (depth, character_id))
    conn.commit()
    conn.close()

def get_item_prefix(level):
    """Получение префикса предмета по уровню"""
    if level <= 4: return ""
    elif level <= 9: return "Стальной"
    elif level <= 14: return "Боевой"
    elif level <= 19: return "Крепкий"
    elif level <= 24: return "Закалённый"
    elif level <= 29: return "Древний"
    elif level <= 34: return "Мифриловый"
    elif level <= 39: return "Адамантовый"
    elif level <= 44: return "Легендарный"
    else: return "Эпический"