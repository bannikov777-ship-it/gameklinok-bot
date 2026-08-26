# core/resources.py
import sqlite3
from config import DB_NAME


def get_player_resources(character_id):
    """Получение ресурсов игрока"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT r.id, r.name, r.icon, r.quantity
        FROM player_resources pr
        JOIN resource_templates r ON pr.resource_id = r.id
        WHERE pr.owner_id = ?
    ''', (character_id,))
    rows = cur.fetchall()
    conn.close()
    
    resources = []
    for row in rows:
        resources.append({
            'id': row[0],
            'name': row[1],
            'icon': row[2],
            'quantity': row[3]
        })
    return resources


def add_resource(character_id, resource_id, quantity):
    """Добавление ресурса игроку"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO player_resources (owner_id, resource_id, quantity)
        VALUES (?, ?, ?)
        ON CONFLICT(owner_id, resource_id) DO UPDATE SET quantity = quantity + ?
    ''', (character_id, resource_id, quantity, quantity))
    conn.commit()
    conn.close()


def remove_resource(character_id, resource_id, quantity):
    """Удаление ресурса у игрока"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT quantity FROM player_resources WHERE owner_id = ? AND resource_id = ?', 
                (character_id, resource_id))
    row = cur.fetchone()
    if not row or row[0] < quantity:
        conn.close()
        return False
    
    if row[0] == quantity:
        cur.execute('DELETE FROM player_resources WHERE owner_id = ? AND resource_id = ?', 
                   (character_id, resource_id))
    else:
        cur.execute('UPDATE player_resources SET quantity = quantity - ? WHERE owner_id = ? AND resource_id = ?', 
                   (quantity, character_id, resource_id))
    conn.commit()
    conn.close()
    return True