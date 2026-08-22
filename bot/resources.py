# resources.py
import sqlite3
import random
from config import DB_NAME

def seed_resources():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM resource_templates')
    if cur.fetchone()[0] > 0:
        conn.close()
        return
    
    resources = [
        ('Шкура', '🩸', 'forest', 1, 15, 'Шкура убитого зверя'),
        ('Коготь', '🐾', 'forest', 1, 12, 'Острый коготь хищника'),
        ('Зуб', '🦷', 'forest', 1, 10, 'Крепкий зуб монстра'),
        ('Магическая эссенция', '✨', 'forest', 2, 25, 'Сгусток магической энергии'),
        ('Древесный гриб', '🍄', 'forest', 1, 8, 'Целебный гриб, растущий на деревьях'),
        ('Волчья шерсть', '🐺', 'forest', 1, 10, 'Тёплая шерсть лесного волка'),
        ('Слеза феи', '🧚', 'forest', 2, 20, 'Застывшая слеза лесной феи'),
        ('Кости', '🦴', 'graveyard', 1, 15, 'Кости древних воинов'),
        ('Прах', '💀', 'graveyard', 1, 12, 'Тёмный прах, оставшийся от нежити'),
        ('Тёмная эссенция', '🌑', 'graveyard', 2, 30, 'Сгусток некротической энергии'),
        ('Гнилая плоть', '🧟', 'graveyard', 1, 10, 'Разлагающаяся плоть мертвеца'),
        ('Старый медальон', '📿', 'graveyard', 2, 20, 'Древний медальон с неизвестным гербом'),
        ('Череп', '☠️', 'graveyard', 1, 18, 'Череп павшего героя'),
        ('Кровавый камень', '🔴', 'graveyard', 2, 28, 'Камень, пропитанный кровью'),
    ]
    cur.executemany('''
        INSERT INTO resource_templates (name, icon, zone, rarity, price, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', resources)
    conn.commit()
    conn.close()

def get_player_resources(owner_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT rt.id, rt.name, rt.icon, rt.rarity, rt.price, pr.quantity
        FROM resource_templates rt
        JOIN player_resources pr ON rt.id = pr.resource_id
        WHERE pr.owner_id = ? AND pr.quantity > 0
    ''', (owner_id,))
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'icon': r[2], 'rarity': r[3], 'price': r[4], 'quantity': r[5]} for r in rows]

def add_resource(owner_id, resource_id, quantity=1):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('INSERT INTO player_resources (owner_id, resource_id, quantity) VALUES (?, ?, ?) '
                'ON CONFLICT(owner_id, resource_id) DO UPDATE SET quantity = quantity + ?',
                (owner_id, resource_id, quantity, quantity))
    conn.commit()
    conn.close()
    return True

def remove_resource(owner_id, resource_id, quantity=1):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT quantity FROM player_resources WHERE owner_id = ? AND resource_id = ?', (owner_id, resource_id))
    row = cur.fetchone()
    if not row or row[0] < quantity:
        conn.close()
        return False
    new_qty = row[0] - quantity
    if new_qty == 0:
        cur.execute('DELETE FROM player_resources WHERE owner_id = ? AND resource_id = ?', (owner_id, resource_id))
    else:
        cur.execute('UPDATE player_resources SET quantity = ? WHERE owner_id = ? AND resource_id = ?', (new_qty, owner_id, resource_id))
    conn.commit()
    conn.close()
    return True

def get_resource_id_by_name(name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM resource_templates WHERE name = ?', (name,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_random_resource_by_zone(zone, tier=1, is_boss=False):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, rarity, price FROM resource_templates WHERE zone = ?', (zone,))
    resources = cur.fetchall()
    conn.close()
    if not resources:
        return None
    max_rarity = min(tier, 3)
    pool = [r for r in resources if r[1] <= max_rarity]
    if not pool:
        pool = resources
    if is_boss:
        weights = [1 + r[1] for r in pool]
        chosen = random.choices(pool, weights=weights, k=1)[0]
    else:
        chosen = random.choice(pool)
    return {'id': chosen[0], 'rarity': chosen[1], 'price': chosen[2]}

def drop_resource_for_monster(zone, tier, is_boss, drop_chance=0.25):
    if random.random() > drop_chance:
        return None
    resource = get_random_resource_by_zone(zone, tier, is_boss)
    if not resource:
        return None
    quantity = random.randint(1, 3) if is_boss else random.randint(1, 2)
    return resource['id'], quantity

def sell_all_resources(owner_id, zone_filter=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    query = '''
        SELECT pr.resource_id, pr.quantity, rt.price
        FROM player_resources pr
        JOIN resource_templates rt ON pr.resource_id = rt.id
        WHERE pr.owner_id = ?
    '''
    params = [owner_id]
    if zone_filter:
        query += ' AND rt.zone = ?'
        params.append(zone_filter)
    cur.execute(query, params)
    resources = cur.fetchall()
    if not resources:
        conn.close()
        return 0, "У вас нет ресурсов для продажи."
    total_silver = 0
    for resource_id, quantity, price in resources:
        total_silver += price * quantity
    if zone_filter:
        cur.execute('''
            DELETE FROM player_resources
            WHERE owner_id = ? AND resource_id IN (SELECT id FROM resource_templates WHERE zone = ?)
        ''', (owner_id, zone_filter))
    else:
        cur.execute('DELETE FROM player_resources WHERE owner_id = ?', (owner_id,))
    cur.execute('UPDATE characters SET silver = silver + ? WHERE id = ?', (total_silver, owner_id))
    conn.commit()
    conn.close()
    return total_silver, f"Вы продали ресурсы и получили {total_silver} серебра."

def get_all_resource_templates():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, name, icon, rarity, price, description, zone FROM resource_templates')
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'icon': r[2], 'rarity': r[3], 'price': r[4], 'description': r[5], 'zone': r[6]} for r in rows]