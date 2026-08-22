# items.py
import sqlite3
import random
from config import DB_NAME

def init_items_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")

    # Удаляем старую таблицу и создаем новую с нужными колонками
    cur.execute("DROP TABLE IF EXISTS item_templates")
    cur.execute('''
        CREATE TABLE item_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            slot TEXT,
            base_attack INTEGER DEFAULT 0,
            base_defense INTEGER DEFAULT 0,
            base_hp INTEGER DEFAULT 0,
            base_mana INTEGER DEFAULT 0,
            growth_attack REAL DEFAULT 0.1,
            growth_defense REAL DEFAULT 0.1,
            growth_hp REAL DEFAULT 0.1,
            growth_mana REAL DEFAULT 0.1,
            icon TEXT DEFAULT '🗡️',
            bonus_crit INTEGER DEFAULT 0,
            bonus_dodge INTEGER DEFAULT 0
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS player_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            template_id INTEGER,
            level INTEGER DEFAULT 1,
            rarity INTEGER DEFAULT 1,
            upgrade_level INTEGER DEFAULT 0,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (owner_id) REFERENCES characters(id),
            FOREIGN KEY (template_id) REFERENCES item_templates(id)
        )
    ''')
    
    cur.execute("DROP TABLE IF EXISTS equipment")
    cur.execute('''
        CREATE TABLE equipment (
            character_id INTEGER,
            slot TEXT,
            player_item_id INTEGER,
            PRIMARY KEY (character_id, slot),
            FOREIGN KEY (character_id) REFERENCES characters(id),
            FOREIGN KEY (player_item_id) REFERENCES player_items(id)
        )
    ''')
    conn.commit()
    conn.close()


def seed_item_templates():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM item_templates')
    if cur.fetchone()[0] == 0:
        templates = [
            # ===== ОРУЖИЕ (Правая рука) =====
            # Меч (баланс) - 5 редкостей
            ('Меч', 'weapon_right', 5, 0, 0, 0, 0.25, 0, 0, 0, '🗡️', 2, 2),
            ('Меч', 'weapon_right', 6, 0, 0, 0, 0.25, 0, 0, 0, '🗡️', 3, 3),
            ('Меч', 'weapon_right', 7, 0, 0, 0, 0.25, 0, 0, 0, '🗡️', 4, 4),
            ('Меч', 'weapon_right', 8, 0, 0, 0, 0.25, 0, 0, 0, '🗡️', 5, 5),
            ('Меч', 'weapon_right', 10, 0, 0, 0, 0.25, 0, 0, 0, '🗡️', 7, 7),
            
            # Молот (сильный урон, низкий крит/уворот) - 5 редкостей
            ('Молот', 'weapon_right', 7, 0, 0, 0, 0.30, 0, 0, 0, '🔨', -5, -5),
            ('Молот', 'weapon_right', 9, 0, 0, 0, 0.30, 0, 0, 0, '🔨', -3, -3),
            ('Молот', 'weapon_right', 11, 0, 0, 0, 0.30, 0, 0, 0, '🔨', -1, -1),
            ('Молот', 'weapon_right', 13, 0, 0, 0, 0.30, 0, 0, 0, '🔨', 1, 1),
            ('Молот', 'weapon_right', 16, 0, 0, 0, 0.30, 0, 0, 0, '🔨', 3, 3),
            
            # Лук (высокий крит/уворот, средний урон) - 5 редкостей
            ('Лук', 'weapon_right', 4, 0, 0, 0, 0.20, 0, 0, 0, '🏹', 8, 8),
            ('Лук', 'weapon_right', 5, 0, 0, 0, 0.20, 0, 0, 0, '🏹', 10, 10),
            ('Лук', 'weapon_right', 6, 0, 0, 0, 0.20, 0, 0, 0, '🏹', 12, 12),
            ('Лук', 'weapon_right', 7, 0, 0, 0, 0.20, 0, 0, 0, '🏹', 15, 15),
            ('Лук', 'weapon_right', 9, 0, 0, 0, 0.20, 0, 0, 0, '🏹', 18, 18),
            
            # ===== БРОНЯ (Торс) =====
            # Кожаная броня (легкая, дает уворот)
            ('Кожаная броня', 'armor', 0, 2, 3, 0, 0, 0.10, 0.05, 0, '🦺', 0, 5),
            ('Кожаная броня', 'armor', 0, 3, 5, 0, 0, 0.10, 0.05, 0, '🦺', 0, 7),
            ('Кожаная броня', 'armor', 0, 4, 7, 0, 0, 0.10, 0.05, 0, '🦺', 0, 10),
            ('Кожаная броня', 'armor', 0, 5, 10, 0, 0, 0.10, 0.05, 0, '🦺', 0, 12),
            ('Кожаная броня', 'armor', 0, 7, 14, 0, 0, 0.10, 0.05, 0, '🦺', 0, 15),
            
            # Кольчуга (средняя, баланс)
            ('Кольчуга', 'armor', 0, 3, 5, 0, 0, 0.15, 0.10, 0, '🛡️', 2, 2),
            ('Кольчуга', 'armor', 0, 5, 8, 0, 0, 0.15, 0.10, 0, '🛡️', 3, 3),
            ('Кольчуга', 'armor', 0, 7, 12, 0, 0, 0.15, 0.10, 0, '🛡️', 4, 4),
            ('Кольчуга', 'armor', 0, 9, 16, 0, 0, 0.15, 0.10, 0, '🛡️', 5, 5),
            ('Кольчуга', 'armor', 0, 12, 22, 0, 0, 0.15, 0.10, 0, '🛡️', 7, 7),
            
            # Кираса (тяжелая, высокая защита)
            ('Кираса', 'armor', 0, 4, 3, 0, 0, 0.20, 0.05, 0, '🛡️', -3, -3),
            ('Кираса', 'armor', 0, 6, 5, 0, 0, 0.20, 0.05, 0, '🛡️', -2, -2),
            ('Кираса', 'armor', 0, 9, 8, 0, 0, 0.20, 0.05, 0, '🛡️', 0, 0),
            ('Кираса', 'armor', 0, 12, 12, 0, 0, 0.20, 0.05, 0, '🛡️', 2, 2),
            ('Кираса', 'armor', 0, 16, 18, 0, 0, 0.20, 0.05, 0, '🛡️', 4, 4),
            
            # ===== ШЛЕМЫ =====
            ('Подшлемник', 'head', 0, 1, 2, 0, 0, 0.08, 0.05, 0, '🎩', 0, 3),
            ('Подшлемник', 'head', 0, 2, 3, 0, 0, 0.08, 0.05, 0, '🎩', 0, 5),
            ('Подшлемник', 'head', 0, 3, 5, 0, 0, 0.08, 0.05, 0, '🎩', 0, 7),
            ('Подшлемник', 'head', 0, 4, 7, 0, 0, 0.08, 0.05, 0, '🎩', 0, 10),
            ('Подшлемник', 'head', 0, 6, 10, 0, 0, 0.08, 0.05, 0, '🎩', 0, 12),
            
            ('Шлем', 'head', 0, 2, 3, 0, 0, 0.12, 0.08, 0, '🎩', 2, 1),
            ('Шлем', 'head', 0, 3, 5, 0, 0, 0.12, 0.08, 0, '🎩', 3, 2),
            ('Шлем', 'head', 0, 5, 8, 0, 0, 0.12, 0.08, 0, '🎩', 4, 3),
            ('Шлем', 'head', 0, 7, 12, 0, 0, 0.12, 0.08, 0, '🎩', 5, 4),
            ('Шлем', 'head', 0, 10, 18, 0, 0, 0.12, 0.08, 0, '🎩', 7, 5),
            
            ('Треуголка', 'head', 0, 3, 2, 0, 0, 0.15, 0.05, 0, '🎩', -2, -2),
            ('Треуголка', 'head', 0, 5, 3, 0, 0, 0.15, 0.05, 0, '🎩', -1, -1),
            ('Треуголка', 'head', 0, 8, 5, 0, 0, 0.15, 0.05, 0, '🎩', 0, 0),
            ('Треуголка', 'head', 0, 11, 8, 0, 0, 0.15, 0.05, 0, '🎩', 2, 1),
            ('Треуголка', 'head', 0, 15, 12, 0, 0, 0.15, 0.05, 0, '🎩', 4, 2),
            
            # ===== САПОГИ =====
            ('Кожаные сапоги', 'boots', 1, 1, 0, 0, 0.10, 0.08, 0, 0, '👢', 0, 4),
            ('Кожаные сапоги', 'boots', 2, 2, 0, 0, 0.10, 0.08, 0, 0, '👢', 0, 6),
            ('Кожаные сапоги', 'boots', 3, 3, 0, 0, 0.10, 0.08, 0, 0, '👢', 0, 8),
            ('Кожаные сапоги', 'boots', 4, 4, 0, 0, 0.10, 0.08, 0, 0, '👢', 0, 10),
            ('Кожаные сапоги', 'boots', 6, 6, 0, 0, 0.10, 0.08, 0, 0, '👢', 0, 13),
            
            ('Железные сапоги', 'boots', 2, 2, 0, 0, 0.12, 0.12, 0, 0, '👢', 2, 2),
            ('Железные сапоги', 'boots', 3, 3, 0, 0, 0.12, 0.12, 0, 0, '👢', 3, 3),
            ('Железные сапоги', 'boots', 5, 5, 0, 0, 0.12, 0.12, 0, 0, '👢', 4, 4),
            ('Железные сапоги', 'boots', 7, 7, 0, 0, 0.12, 0.12, 0, 0, '👢', 5, 5),
            ('Железные сапоги', 'boots', 10, 10, 0, 0, 0.12, 0.12, 0, 0, '👢', 7, 7),
            
            ('Стальные сапоги', 'boots', 3, 3, 0, 0, 0.15, 0.15, 0, 0, '👢', -3, -3),
            ('Стальные сапоги', 'boots', 5, 5, 0, 0, 0.15, 0.15, 0, 0, '👢', -2, -2),
            ('Стальные сапоги', 'boots', 8, 8, 0, 0, 0.15, 0.15, 0, 0, '👢', 0, 0),
            ('Стальные сапоги', 'boots', 11, 11, 0, 0, 0.15, 0.15, 0, 0, '👢', 2, 2),
            ('Стальные сапоги', 'boots', 15, 15, 0, 0, 0.15, 0.15, 0, 0, '👢', 4, 4),
        ]
        cur.executemany('''
            INSERT INTO item_templates (name, slot, base_attack, base_defense, base_hp, base_mana, 
                                        growth_attack, growth_defense, growth_hp, growth_mana, icon,
                                        bonus_crit, bonus_dodge)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', templates)
        conn.commit()
    conn.close()


def get_item_template_id_by_name(name):
    """Возвращает ID первого найденного шаблона по имени"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM item_templates WHERE name = ? LIMIT 1', (name,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_item_stats(template_id, level, rarity, upgrade_level):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''SELECT name, slot, base_attack, base_defense, base_hp, base_mana,
                          growth_attack, growth_defense, growth_hp, growth_mana, icon,
                          bonus_crit, bonus_dodge
                   FROM item_templates WHERE id = ?''', (template_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    
    name, slot, base_attack, base_defense, base_hp, base_mana, g_attack, g_defense, g_hp, g_mana, icon, bonus_crit, bonus_dodge = row
    
    rarity_mult = {1:1.0, 2:1.2, 3:1.35, 4:1.5, 5:1.7}.get(rarity, 1.0)
    upgrade_bonus = 1 + 0.2 * upgrade_level
    
    def calc(base, growth):
        return base * (1 + (level - 1) * growth)
    
    final_attack = calc(base_attack, g_attack) * rarity_mult * upgrade_bonus
    final_defense = calc(base_defense, g_defense) * rarity_mult * upgrade_bonus
    final_hp = calc(base_hp, g_hp) * rarity_mult * upgrade_bonus
    final_mana = calc(base_mana, g_mana) * rarity_mult * upgrade_bonus
    
    final_crit = bonus_crit * rarity_mult if bonus_crit else 0
    final_dodge = bonus_dodge * rarity_mult if bonus_dodge else 0
    
    return {
        'name': name,
        'slot': slot,
        'attack': round(final_attack),
        'defense': round(final_defense),
        'hp': round(final_hp),
        'mana': round(final_mana),
        'icon': icon,
        'bonus_crit': round(final_crit),
        'bonus_dodge': round(final_dodge)
    }


def create_player_item(owner_id, template_id, level, rarity):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO player_items (owner_id, template_id, level, rarity, upgrade_level, quantity)
        VALUES (?, ?, ?, ?, ?, 1)
    ''', (owner_id, template_id, level, rarity, 0))
    item_id = cur.lastrowid
    conn.commit()
    conn.close()
    return item_id


def create_player_item_with_rarity(owner_id, template_id, level, rarity):
    """Создает предмет с указанной редкостью"""
    return create_player_item(owner_id, template_id, level, rarity)


def get_player_items(owner_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''SELECT pi.id, pi.template_id, pi.level, pi.rarity, pi.upgrade_level, pi.quantity
                   FROM player_items pi
                   LEFT JOIN equipment e ON pi.id = e.player_item_id
                   WHERE pi.owner_id = ? AND e.player_item_id IS NULL
                ''', (owner_id,))
    rows = cur.fetchall()
    conn.close()
    items = []
    for row in rows:
        item_id, template_id, level, rarity, upgrade, qty = row
        stats = get_item_stats(template_id, level, rarity, upgrade)
        if stats:
            stats['id'] = item_id
            stats['template_id'] = template_id
            stats['level'] = level
            stats['rarity'] = rarity
            stats['upgrade_level'] = upgrade
            stats['quantity'] = qty
            items.append(stats)
    return items


def get_equipped_items(character_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT equipment.slot, player_items.id, player_items.template_id, player_items.level, player_items.rarity, player_items.upgrade_level
        FROM equipment
        JOIN player_items ON equipment.player_item_id = player_items.id
        WHERE equipment.character_id = ?
    ''', (character_id,))
    rows = cur.fetchall()
    conn.close()
    equipped = {}
    for row in rows:
        slot, item_id, template_id, level, rarity, upgrade = row
        stats = get_item_stats(template_id, level, rarity, upgrade)
        if stats:
            stats['id'] = item_id
            stats['slot'] = slot
            stats['rarity'] = rarity
            stats['upgrade_level'] = upgrade
            equipped[slot] = stats
    return equipped


def equip_item(character_id, player_item_id, slot):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT owner_id, template_id, level, rarity, upgrade_level, quantity FROM player_items WHERE id = ?', (player_item_id,))
    row = cur.fetchone()
    if not row or row[0] != character_id:
        conn.close()
        return False
    owner_id, template_id, level, rarity, upgrade_level, quantity = row

    cur.execute('SELECT player_item_id FROM equipment WHERE character_id = ? AND slot = ?', (character_id, slot))
    old = cur.fetchone()
    if old:
        old_item_id = old[0]
        cur.execute('SELECT template_id, level, rarity, upgrade_level FROM player_items WHERE id = ?', (old_item_id,))
        old_data = cur.fetchone()
        if old_data:
            cur.execute('INSERT INTO player_items (owner_id, template_id, level, rarity, upgrade_level, quantity) VALUES (?, ?, ?, ?, ?, 1)',
                        (character_id, old_data[0], old_data[1], old_data[2], old_data[3]))
        cur.execute('DELETE FROM equipment WHERE character_id = ? AND slot = ?', (character_id, slot))
        cur.execute('DELETE FROM player_items WHERE id = ?', (old_item_id,))

    if quantity > 1:
        cur.execute('UPDATE player_items SET quantity = quantity - 1 WHERE id = ?', (player_item_id,))
    else:
        cur.execute('DELETE FROM player_items WHERE id = ?', (player_item_id,))

    cur.execute('INSERT INTO player_items (owner_id, template_id, level, rarity, upgrade_level, quantity) VALUES (?, ?, ?, ?, ?, 1)',
                (character_id, template_id, level, rarity, upgrade_level))
    new_item_id = cur.lastrowid
    cur.execute('INSERT INTO equipment (character_id, slot, player_item_id) VALUES (?, ?, ?)',
                (character_id, slot, new_item_id))
    conn.commit()
    conn.close()
    return True


def unequip_item(character_id, slot):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT player_item_id FROM equipment WHERE character_id = ? AND slot = ?', (character_id, slot))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    item_id = row[0]
    cur.execute('SELECT template_id, level, rarity, upgrade_level FROM player_items WHERE id = ?', (item_id,))
    data = cur.fetchone()
    if not data:
        conn.close()
        return False
    cur.execute('DELETE FROM equipment WHERE character_id = ? AND slot = ?', (character_id, slot))
    cur.execute('DELETE FROM player_items WHERE id = ?', (item_id,))
    cur.execute('INSERT INTO player_items (owner_id, template_id, level, rarity, upgrade_level, quantity) VALUES (?, ?, ?, ?, ?, 1)',
                (character_id, data[0], data[1], data[2], data[3]))
    conn.commit()
    conn.close()
    return True


def generate_shop_item(owner_id, template_name, level):
    template_id = get_item_template_id_by_name(template_name)
    if not template_id:
        return None
    item_id = create_player_item(owner_id, template_id, level, rarity=1)
    return item_id


def upgrade_item(player_item_id, crystal_id=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''SELECT owner_id, template_id, level, rarity, upgrade_level 
                   FROM player_items WHERE id = ?''', (player_item_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None, "Предмет не найден"
    owner_id, template_id, level, rarity, upgrade_level = row

    if upgrade_level >= 10:
        conn.close()
        return None, "Предмет уже имеет максимальный уровень заточки (+10)"

    rarity_price_mult = {1: 250, 2: 350, 3: 550, 4: 750, 5: 1250}
    price = 100 + rarity_price_mult.get(rarity, 250) * upgrade_level

    cur.execute('SELECT silver FROM characters WHERE id = ?', (owner_id,))
    silver_row = cur.fetchone()
    if not silver_row or silver_row[0] < price:
        conn.close()
        return None, f"Недостаточно серебра! Нужно {price}💰"

    if upgrade_level < 3:
        base_chance = 100
    else:
        base_chance = 100 - (upgrade_level - 2) * 10

    crystal_bonus = 0
    if crystal_id:
        cur.execute('SELECT quantity, restore_percent FROM player_consumables WHERE owner_id = ? AND id = ? AND restore_type = "crystal"', (owner_id, crystal_id))
        crystal_row = cur.fetchone()
        if not crystal_row or crystal_row[0] <= 0:
            conn.close()
            return None, "У вас нет такого кристалла"
        crystal_bonus = crystal_row[1]
        new_qty = crystal_row[0] - 1
        if new_qty == 0:
            cur.execute('DELETE FROM player_consumables WHERE owner_id = ? AND id = ?', (owner_id, crystal_id))
        else:
            cur.execute('UPDATE player_consumables SET quantity = ? WHERE owner_id = ? AND id = ?', (new_qty, owner_id, crystal_id))

    final_chance = min(100, base_chance + crystal_bonus)

    cur.execute('UPDATE characters SET silver = silver - ? WHERE id = ?', (price, owner_id))

    success = random.random() * 100 < final_chance

    if success:
        new_level = upgrade_level + 1
        cur.execute('UPDATE player_items SET upgrade_level = ? WHERE id = ?', (new_level, player_item_id))
        conn.commit()
        conn.close()
        from core import recalc_stats
        recalc_stats(owner_id)
        return True, f"Успех! Предмет улучшен до +{new_level}. Шанс был {final_chance}%."
    else:
        if upgrade_level >= 5:
            new_level = upgrade_level - 1
            cur.execute('UPDATE player_items SET upgrade_level = ? WHERE id = ?', (new_level, player_item_id))
            conn.commit()
            conn.close()
            from core import recalc_stats
            recalc_stats(owner_id)
            return False, f"Неудача! Предмет понижен до +{new_level}. Шанс был {final_chance}%."
        else:
            conn.commit()
            conn.close()
            return False, f"Неудача! Уровень заточки остался +{upgrade_level}. Шанс был {final_chance}%."