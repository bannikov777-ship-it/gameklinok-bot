# core/user.py
import sqlite3
import json
from config import DB_NAME

def get_user(vk_id):
    """Получение пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT state, context FROM users WHERE vk_id = ?', (vk_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {'state': row[0], 'context': json.loads(row[1])}
    else:
        add_user(vk_id)
        return {'state': 'city', 'context': {}}

def add_user(vk_id):
    """Добавление пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users (vk_id, state, context) VALUES (?, ?, ?)',
                (vk_id, 'city', '{}'))
    conn.commit()
    conn.close()

def update_user(vk_id, state=None, context=None):
    """Обновление пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if state is not None:
        cur.execute('UPDATE users SET state = ? WHERE vk_id = ?', (state, vk_id))
    if context is not None:
        cur.execute('UPDATE users SET context = ? WHERE vk_id = ?', (json.dumps(context), vk_id))
    conn.commit()
    conn.close()