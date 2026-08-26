# codes.py
import sqlite3
import random
import string
from datetime import datetime, timedelta
from config import DB_NAME


def generate_code(length=8):
    """Генерация случайного кода"""
    characters = string.ascii_uppercase + string.digits
    # Исключаем похожие символы: 0, O, 1, I
    exclude = '0O1I'
    chars = [c for c in characters if c not in exclude]
    return ''.join(random.choice(chars) for _ in range(length))


def create_code(amount, expires_days=30, max_uses=1, description=""):
    """
    Создание нового кода
    
    Args:
        amount (int): количество кристаллов
        expires_days (int): срок действия в днях
        max_uses (int): максимальное количество использований (1 = одноразовый)
        description (str): описание кода
    
    Returns:
        str: сгенерированный код
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Проверяем, существует ли таблица
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='promo_codes'")
    if not cur.fetchone():
        # Создаём таблицу
        cur.execute('''
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                amount INTEGER NOT NULL,
                max_uses INTEGER DEFAULT 1,
                used_count INTEGER DEFAULT 0,
                expires_at TIMESTAMP,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS promo_code_uses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_id INTEGER,
                character_id INTEGER,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                amount INTEGER,
                FOREIGN KEY (code_id) REFERENCES promo_codes(id),
                FOREIGN KEY (character_id) REFERENCES characters(id),
                UNIQUE(code_id, character_id)
            )
        ''')
        conn.commit()
    
    # Генерируем уникальный код
    while True:
        code = generate_code(8)
        cur.execute('SELECT id FROM promo_codes WHERE code = ?', (code,))
        if not cur.fetchone():
            break
    
    expires_at = datetime.now() + timedelta(days=expires_days)
    
    cur.execute('''
        INSERT INTO promo_codes (code, amount, max_uses, expires_at, description, created_by)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (code, amount, max_uses, expires_at.isoformat(), description, 1))  # created_by = 1 (админ)
    
    conn.commit()
    conn.close()
    return code


def use_code(character_id, code):
    """
    Использование кода
    
    Args:
        character_id (int): ID персонажа
        code (str): код для активации
    
    Returns:
        tuple: (success, message, amount, reward_type)
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Проверяем существование таблицы
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='promo_codes'")
    if not cur.fetchone():
        conn.close()
        return False, "Система промокодов ещё не активирована.", 0, None
    
    # Ищем код
    cur.execute('''
        SELECT id, amount, max_uses, used_count, expires_at, is_active, reward_type
        FROM promo_codes WHERE code = ?
    ''', (code.upper(),))
    row = cur.fetchone()
    
    if not row:
        conn.close()
        return False, "❌ Неверный код.", 0, None
    
    code_id, amount, max_uses, used_count, expires_at, is_active, reward_type = row
    reward_type = reward_type or 'crystals'  # по умолчанию кристаллы
    
    # Проверяем активность
    if not is_active:
        conn.close()
        return False, "❌ Код деактивирован.", 0, None
    
    # Проверяем срок действия
    if expires_at:
        if datetime.now() > datetime.fromisoformat(expires_at):
            conn.close()
            return False, "❌ Срок действия кода истёк.", 0, None
    
    # Проверяем количество использований
    if used_count >= max_uses:
        conn.close()
        return False, "❌ Код уже использован.", 0, None
    
    # Проверяем, использовал ли уже этот игрок код
    cur.execute('SELECT id FROM promo_code_uses WHERE code_id = ? AND character_id = ?', 
                (code_id, character_id))
    if cur.fetchone():
        conn.close()
        return False, "❌ Вы уже использовали этот код.", 0, None
    
    # Начисляем награду (кристаллы или серебро)
    if reward_type == 'silver':
        cur.execute('UPDATE characters SET silver = silver + ? WHERE id = ?', 
                    (amount, character_id))
    else:
        cur.execute('UPDATE characters SET crystals = crystals + ? WHERE id = ?', 
                    (amount, character_id))
    
    # Увеличиваем счётчик использований
    cur.execute('UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?', 
                (code_id,))
    
    # Записываем использование
    cur.execute('''
        INSERT INTO promo_code_uses (code_id, character_id, amount)
        VALUES (?, ?, ?)
    ''', (code_id, character_id, amount))
    
    conn.commit()
    conn.close()
    
    reward_icon = '💰 серебра' if reward_type == 'silver' else '💎 кристаллов'
    return True, f"✅ Код активирован! Вы получили {amount} {reward_icon}!", amount, reward_type


def get_codes_stats():
    """Получение статистики по кодам"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(amount) as total_amount,
            SUM(used_count) as total_uses
        FROM promo_codes
        WHERE is_active = 1
    ''')
    row = cur.fetchone()
    conn.close()
    
    return {
        'total': row[0] or 0,
        'total_amount': row[1] or 0,
        'total_uses': row[2] or 0
    }


def get_codes_list(limit=20):
    """Получение списка кодов"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT code, amount, max_uses, used_count, expires_at, description, created_at, is_active
        FROM promo_codes
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    rows = cur.fetchall()
    conn.close()
    
    codes = []
    for row in rows:
        codes.append({
            'code': row[0],
            'amount': row[1],
            'max_uses': row[2],
            'used_count': row[3],
            'expires_at': row[4],
            'description': row[5],
            'created_at': row[6],
            'is_active': row[7]
        })
    return codes