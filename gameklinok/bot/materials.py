# materials.py
import sqlite3
import json
from config import DB_NAME

def sell_all_materials(player_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT materials FROM characters WHERE id = ?', (player_id,))
    row = cur.fetchone()
    materials = json.loads(row[0]) if row and row[0] else {}
    if not materials:
        conn.close()
        return 0, "У вас нет трофеев для продажи."
    total_silver = 0
    total_items = 0
    for material, count in materials.items():
        price = 150
        total_silver += price * count
        total_items += count
    cur.execute('UPDATE characters SET materials = "{}" WHERE id = ?', (player_id,))
    cur.execute('UPDATE characters SET silver = silver + ? WHERE id = ?', (total_silver, player_id))
    conn.commit()
    conn.close()
    return total_silver, f"Вы продали {total_items} трофеев и получили {total_silver} серебра."