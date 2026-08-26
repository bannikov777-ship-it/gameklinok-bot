# auction.py
import sqlite3
import asyncio
from config import DB_NAME

def create_auction_lot(seller_type, seller_id, item_type, item_id, quantity, price):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if item_type == 'item':
        cur.execute('SELECT template_id, level, rarity, upgrade_level, quantity FROM player_items WHERE id = ? AND owner_id = ?', (item_id, seller_id))
        row = cur.fetchone()
        if not row:
            conn.close()
            return None, "Предмет не найден."
        template_id, level, rarity, upgrade_level, qty = row
        if qty < quantity:
            conn.close()
            return None, "Недостаточно предметов."
        new_qty = qty - quantity
        if new_qty == 0:
            cur.execute('DELETE FROM player_items WHERE id = ?', (item_id,))
        else:
            cur.execute('UPDATE player_items SET quantity = ? WHERE id = ?', (new_qty, item_id))
        cur.execute('''
            INSERT INTO auction_lots (seller_type, seller_id, item_type, template_id, level, rarity, upgrade_level, quantity, price, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+24 hours'))
        ''', (seller_type, seller_id, item_type, template_id, level, rarity, upgrade_level, quantity, price))
        lot_id = cur.lastrowid
        conn.commit()
        conn.close()
        return lot_id, "Лот создан."
    else:
        cur.execute('SELECT consumable_template_id, quantity FROM player_consumables WHERE id = ? AND owner_id = ?', (item_id, seller_id))
        row = cur.fetchone()
        if not row:
            conn.close()
            return None, "Расходник не найден."
        template_id, qty = row
        if qty < quantity:
            conn.close()
            return None, "Недостаточно расходников."
        new_qty = qty - quantity
        if new_qty == 0:
            cur.execute('DELETE FROM player_consumables WHERE id = ?', (item_id,))
        else:
            cur.execute('UPDATE player_consumables SET quantity = ? WHERE id = ?', (new_qty, item_id))
        cur.execute('''
            INSERT INTO auction_lots (seller_type, seller_id, item_type, template_id, quantity, price, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now', '+24 hours'))
        ''', (seller_type, seller_id, item_type, template_id, quantity, price))
        lot_id = cur.lastrowid
        conn.commit()
        conn.close()
        return lot_id, "Лот создан."

def get_active_auction_lots(limit=20, offset=0):
    expire_and_return_expired()
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT id, seller_type, seller_id, item_type, template_id, level, rarity, upgrade_level, quantity, price
        FROM auction_lots
        WHERE status = 'active' AND expires_at > datetime('now')
        ORDER BY id ASC
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    rows = cur.fetchall()
    conn.close()
    lots = []
    for row in rows:
        lot = {
            'id': row[0],
            'seller_type': row[1],
            'seller_id': row[2],
            'item_type': row[3],
            'template_id': row[4],
            'level': row[5],
            'rarity': row[6],
            'upgrade_level': row[7],
            'quantity': row[8],
            'price': row[9]
        }
        if lot['item_type'] == 'item':
            conn2 = sqlite3.connect(DB_NAME)
            cur2 = conn2.cursor()
            cur2.execute('SELECT name, icon, base_attack, base_defense, base_hp, base_mana, growth_attack, growth_defense, growth_hp, growth_mana FROM item_templates WHERE id = ?', (lot['template_id'],))
            item_info = cur2.fetchone()
            conn2.close()
            if item_info:
                name, icon, base_atk, base_def, base_hp, base_mana, g_atk, g_def, g_hp, g_mana = item_info
                rarity_mult = {1:1.0, 2:1.2, 3:1.35, 4:1.5, 5:1.7}.get(lot['rarity'], 1.0)
                upgrade_bonus = 1 + 0.2 * lot['upgrade_level']
                def calc(base, growth):
                    return base * (1 + (lot['level'] - 1) * growth)
                lot['name'] = name
                lot['icon'] = icon
                lot['attack'] = round(calc(base_atk, g_atk) * rarity_mult * upgrade_bonus)
                lot['defense'] = round(calc(base_def, g_def) * rarity_mult * upgrade_bonus)
                lot['hp'] = round(calc(base_hp, g_hp) * rarity_mult * upgrade_bonus)
                lot['mana'] = round(calc(base_mana, g_mana) * rarity_mult * upgrade_bonus)
            else:
                lot['name'] = 'Неизвестный предмет'
                lot['icon'] = '❓'
                lot['attack'] = 0
                lot['defense'] = 0
                lot['hp'] = 0
                lot['mana'] = 0
        else:
            conn2 = sqlite3.connect(DB_NAME)
            cur2 = conn2.cursor()
            cur2.execute('SELECT name, icon, restore_type, restore_percent FROM consumable_templates WHERE id = ?', (lot['template_id'],))
            item_info = cur2.fetchone()
            conn2.close()
            if item_info:
                lot['name'] = item_info[0]
                lot['icon'] = item_info[1]
                lot['restore_type'] = item_info[2]
                lot['restore_percent'] = item_info[3]
            else:
                lot['name'] = 'Неизвестный расходник'
                lot['icon'] = '❓'
        lots.append(lot)
    return lots

def expire_and_return_expired():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT id, seller_type, seller_id, item_type, template_id, level, rarity, upgrade_level, quantity
        FROM auction_lots
        WHERE status = 'active' AND expires_at <= datetime('now')
    ''')
    expired = cur.fetchall()
    for lot in expired:
        lot_id, seller_type, seller_id, item_type, template_id, level, rarity, upgrade_level, quantity = lot
        if item_type == 'item':
            cur.execute('INSERT INTO player_items (owner_id, template_id, level, rarity, upgrade_level, quantity) VALUES (?, ?, ?, ?, ?, ?)',
                        (seller_id, template_id, level, rarity, upgrade_level, quantity))
        else:
            cur.execute('INSERT INTO player_consumables (owner_id, consumable_template_id, quantity) VALUES (?, ?, ?) '
                        'ON CONFLICT(owner_id, consumable_template_id) DO UPDATE SET quantity = quantity + ?',
                        (seller_id, template_id, quantity, quantity))
        cur.execute('UPDATE auction_lots SET status = "expired" WHERE id = ?', (lot_id,))
    conn.commit()
    conn.close()

def buy_auction_lot(lot_id, buyer_character_id):
    expire_and_return_expired()
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT seller_type, seller_id, item_type, template_id, level, rarity, upgrade_level, quantity, price FROM auction_lots WHERE id = ? AND status = "active" AND expires_at > datetime("now")', (lot_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Лот уже неактивен."
    seller_type, seller_id, item_type, template_id, level, rarity, upgrade_level, quantity, price = row
    if seller_type == 'player' and seller_id == buyer_character_id:
        conn.close()
        return False, "Нельзя купить свой лот."
    cur.execute('SELECT silver FROM characters WHERE id = ?', (buyer_character_id,))
    buyer_silver = cur.fetchone()
    if not buyer_silver or buyer_silver[0] < price:
        conn.close()
        return False, f"Недостаточно серебра! Нужно {price}💰."
    cur.execute('UPDATE characters SET silver = silver - ? WHERE id = ?', (price, buyer_character_id))
    if item_type == 'item':
        cur.execute('INSERT INTO player_items (owner_id, template_id, level, rarity, upgrade_level, quantity) VALUES (?, ?, ?, ?, ?, ?)',
                    (buyer_character_id, template_id, level, rarity, upgrade_level, quantity))
    else:
        cur.execute('INSERT INTO player_consumables (owner_id, consumable_template_id, quantity) VALUES (?, ?, ?) '
                    'ON CONFLICT(owner_id, consumable_template_id) DO UPDATE SET quantity = quantity + ?',
                    (buyer_character_id, template_id, quantity, quantity))
    if seller_type == 'player':
        cur.execute('UPDATE characters SET silver = silver + ? WHERE id = ?', (price, seller_id))
    else:
        cur.execute('UPDATE guilds SET silver = silver + ? WHERE id = ?', (price, seller_id))
    cur.execute('UPDATE auction_lots SET status = "sold" WHERE id = ?', (lot_id,))
    conn.commit()
    conn.close()
    return True, f"✅ Вы купили {quantity}x за {price}💰."

def get_lot_by_id(lot_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, seller_type, seller_id, item_type, template_id, level, rarity, upgrade_level, quantity, price FROM auction_lots WHERE id = ? AND status = "active" AND expires_at > datetime("now")', (lot_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        'id': row[0],
        'seller_type': row[1],
        'seller_id': row[2],
        'item_type': row[3],
        'template_id': row[4],
        'level': row[5],
        'rarity': row[6],
        'upgrade_level': row[7],
        'quantity': row[8],
        'price': row[9]
    }