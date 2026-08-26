# core/async_wrappers.py
import asyncio
import sqlite3
from config import DB_NAME
from .user import get_user, update_user
from .character import get_character, get_character_by_id
from .stats import recalc_stats

_db_lock = asyncio.Lock()

async def get_user_async(vk_id):
    async with _db_lock:
        return await asyncio.to_thread(get_user, vk_id)

async def update_user_async(vk_id, state=None, context=None):
    async with _db_lock:
        return await asyncio.to_thread(update_user, vk_id, state, context)

async def get_character_async(vk_id):
    async with _db_lock:
        return await asyncio.to_thread(get_character, vk_id)

async def get_character_by_id_async(character_id):
    async with _db_lock:
        return await asyncio.to_thread(get_character_by_id, character_id)

async def recalc_stats_async(character_id):
    async with _db_lock:
        return await asyncio.to_thread(recalc_stats, character_id)

# Функции для работы с расходниками
def get_player_consumables(owner_id):
    import sqlite3
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT ct.id, ct.name, ct.icon, ct.restore_type, ct.restore_percent, pc.quantity
        FROM consumable_templates ct
        JOIN player_consumables pc ON ct.id = pc.consumable_template_id
        WHERE pc.owner_id = ? AND pc.quantity > 0
    ''', (owner_id,))
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'icon': r[2], 'restore_type': r[3], 'restore_percent': r[4], 'quantity': r[5]} for r in rows]

def get_player_crystals(owner_id):
    import sqlite3
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT pc.id, ct.name, ct.icon, ct.restore_percent, pc.quantity
        FROM player_consumables pc
        JOIN consumable_templates ct ON pc.consumable_template_id = ct.id
        WHERE pc.owner_id = ? AND ct.restore_type = 'crystal' AND pc.quantity > 0
    ''', (owner_id,))
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'icon': r[2], 'bonus': r[3], 'quantity': r[4]} for r in rows]

def buy_consumable(owner_id, template_id, quantity=1):
    import sqlite3
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT price FROM consumable_templates WHERE id = ?', (template_id,))
    price_row = cur.fetchone()
    if not price_row:
        conn.close()
        return False, "Шаблон не найден"
    price = price_row[0] * quantity
    cur.execute('SELECT silver FROM characters WHERE id = ?', (owner_id,))
    silver_row = cur.fetchone()
    if not silver_row or silver_row[0] < price:
        conn.close()
        return False, f"Недостаточно серебра! Нужно {price}💰"
    cur.execute('UPDATE characters SET silver = silver - ? WHERE id = ?', (price, owner_id))
    cur.execute('INSERT INTO player_consumables (owner_id, consumable_template_id, quantity) VALUES (?, ?, ?) '
                'ON CONFLICT(owner_id, consumable_template_id) DO UPDATE SET quantity = quantity + ?',
                (owner_id, template_id, quantity, quantity))
    conn.commit()
    conn.close()
    return True, f"Куплено {quantity} шт. за {price}💰"

def use_consumable(owner_id, template_id):
    import sqlite3
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT quantity FROM player_consumables WHERE owner_id = ? AND consumable_template_id = ?', (owner_id, template_id))
    row = cur.fetchone()
    if not row or row[0] <= 0:
        conn.close()
        return None, "Нет зелья"
    new_qty = row[0] - 1
    if new_qty == 0:
        cur.execute('DELETE FROM player_consumables WHERE owner_id = ? AND consumable_template_id = ?', (owner_id, template_id))
    else:
        cur.execute('UPDATE player_consumables SET quantity = ? WHERE owner_id = ? AND consumable_template_id = ?', (new_qty, owner_id, template_id))
    cur.execute('SELECT restore_type, restore_percent FROM consumable_templates WHERE id = ?', (template_id,))
    templ = cur.fetchone()
    conn.commit()
    conn.close()
    if not templ:
        return None, "Ошибка шаблона"
    return (templ[0], templ[1]), None

def get_consumable_templates():
    import sqlite3
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, name, description, icon, restore_type, restore_percent, price FROM consumable_templates')
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'description': r[2], 'icon': r[3], 'restore_type': r[4], 'restore_percent': r[5], 'price': r[6]} for r in rows]

def get_player_herbs(owner_id):
    import sqlite3
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT h.id, h.name, h.icon, h.price, ph.quantity
        FROM herbs h
        JOIN player_herbs ph ON h.id = ph.herb_id
        WHERE ph.owner_id = ? AND ph.quantity > 0
    ''', (owner_id,))
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'icon': r[2], 'price': r[3], 'quantity': r[4]} for r in rows]

def add_herb(owner_id, herb_id, quantity=1):
    import sqlite3
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('INSERT INTO player_herbs (owner_id, herb_id, quantity) VALUES (?, ?, ?) '
                'ON CONFLICT(owner_id, herb_id) DO UPDATE SET quantity = quantity + ?',
                (owner_id, herb_id, quantity, quantity))
    conn.commit()
    conn.close()
    return True

def sell_all_herbs(owner_id):
    import sqlite3
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT herb_id, quantity, price FROM player_herbs ph JOIN herbs h ON ph.herb_id = h.id WHERE owner_id = ?', (owner_id,))
    herbs = cur.fetchall()
    if not herbs:
        conn.close()
        return 0, "У вас нет трав для продажи."
    total_silver = 0
    for herb_id, quantity, price in herbs:
        total_silver += price * quantity
    cur.execute('DELETE FROM player_herbs WHERE owner_id = ?', (owner_id,))
    cur.execute('UPDATE characters SET silver = silver + ? WHERE id = ?', (total_silver, owner_id))
    conn.commit()
    conn.close()
    return total_silver, f"Вы продали все травы и получили {total_silver} серебра."