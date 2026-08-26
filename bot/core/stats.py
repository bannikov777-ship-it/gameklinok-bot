# core/stats.py
import sqlite3
from config import DB_NAME
from items import get_equipped_items

CLASS_BASE_STATS = {
    'Оруженосец': {'attack': 8, 'defense': 5, 'hp': 150, 'mana': 10, 'stamina': 60, 'crit': 3, 'dodge': 3},
    'Охотник': {'attack': 18, 'defense': 1, 'hp': 90, 'mana': 20, 'stamina': 50, 'crit': 8, 'dodge': 8},
    'Послушник': {'attack': 8, 'defense': 2, 'hp': 100, 'mana': 80, 'stamina': 40, 'crit': 4, 'dodge': 4}
}

CLASS_GROWTH = {
    'Оруженосец': {'attack': 1, 'defense': 2, 'hp': 12, 'mana': 2, 'stamina': 4, 'crit': 0.3, 'dodge': 0.3},
    'Охотник': {'attack': 3, 'defense': 0, 'hp': 8, 'mana': 4, 'stamina': 3, 'crit': 1, 'dodge': 1},
    'Послушник': {'attack': 1, 'defense': 1, 'hp': 8, 'mana': 10, 'stamina': 2, 'crit': 0.4, 'dodge': 0.4}
}

NEUTRAL_STATS = {'attack': 10, 'defense': 2, 'hp': 100, 'mana': 20, 'stamina': 50, 'crit': 5, 'dodge': 5}
NEUTRAL_GROWTH = {'attack': 1, 'defense': 1, 'hp': 10, 'mana': 5, 'stamina': 3, 'crit': 0.3, 'dodge': 0.3}

def recalc_stats(character_id):
    """Пересчет характеристик персонажа"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT class, level, debuff FROM characters WHERE id = ?', (character_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return
    class_name, level, debuff = row
    
    if not class_name or class_name == "Неизвестный":
        base = NEUTRAL_STATS
        growth = NEUTRAL_GROWTH
    else:
        base = CLASS_BASE_STATS[class_name]
        growth = CLASS_GROWTH[class_name]
    
    level_bonus = (level - 1)
    base_attack = base['attack'] + growth['attack'] * level_bonus
    base_defense = base['defense'] + growth['defense'] * level_bonus
    base_hp = base['hp'] + growth['hp'] * level_bonus
    base_mana = base['mana'] + growth['mana'] * level_bonus
    base_stamina = base['stamina'] + growth['stamina'] * level_bonus
    base_crit = base['crit'] + growth['crit'] * level_bonus
    base_dodge = base['dodge'] + growth['dodge'] * level_bonus
    
    # Применение дебаффа
    if debuff == 1:
        base_attack = int(base_attack * 0.7)
        base_defense = int(base_defense * 0.7)
        base_hp = int(base_hp * 0.7)
        base_mana = int(base_mana * 0.7)
        base_stamina = int(base_stamina * 0.7)
    elif debuff == 2:
        base_attack = int(base_attack * 0.5)
        base_defense = int(base_defense * 0.5)
        base_hp = int(base_hp * 0.5)
        base_mana = int(base_mana * 0.5)
        base_stamina = int(base_stamina * 0.5)
    
    # Добавление бонусов от экипировки
    equipped = get_equipped_items(character_id)
    
    # ИНИЦИАЛИЗИРУЕМ ПЕРЕМЕННЫЕ ДО ЦИКЛА
    crit_bonus = 0
    dodge_bonus = 0
    
    for slot, item in equipped.items():
        base_attack += item.get('attack', 0)
        base_defense += item.get('defense', 0)
        base_hp += item.get('hp', 0)
        base_mana += item.get('mana', 0)
        crit_bonus += item.get('bonus_crit', 0)
        dodge_bonus += item.get('bonus_dodge', 0)
    
    # Итоговые крит и уворот
    final_crit = max(0, base_crit + crit_bonus)
    final_dodge = max(0, base_dodge + dodge_bonus)
    
    cur.execute('''UPDATE characters
                   SET attack = ?, defense = ?, max_hp = ?, max_mana = ?, 
                       max_stamina = ?, crit_chance = ?, dodge_chance = ?
                   WHERE id = ?''', 
                (base_attack, base_defense, base_hp, base_mana, base_stamina, round(final_crit), round(final_dodge), character_id))
    cur.execute('UPDATE characters SET hp = MIN(hp, max_hp), mana = MIN(mana, max_mana), stamina = MIN(stamina, max_stamina) WHERE id = ?', (character_id,))
    conn.commit()
    conn.close()