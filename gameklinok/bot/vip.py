# vip.py
import sqlite3
import json
from datetime import datetime, timedelta
from config import DB_NAME

# Цвета для VIP
VIP_COLORS = {
    1: '🟫',   # Бронза
    2: '⬜',   # Серебро
    3: '🌟',   # Золото
    4: '💎',   # Платина
    5: '👑'    # Алмаз
}

VIP_NAMES = {
    1: 'Бронзовый',
    2: 'Серебряный',
    3: 'Золотой',
    4: 'Платиновый',
    5: 'Алмазный'
}

VIP_BONUSES = {
    1: {'exp': 10, 'silver': 10},
    2: {'exp': 25, 'silver': 25},
    3: {'exp': 50, 'silver': 50},
    4: {'exp': 75, 'silver': 75},
    5: {'exp': 100, 'silver': 100}
}


def get_vip(character_id):
    """Получение VIP-статуса персонажа"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Проверяем, есть ли колонка vip
    cur.execute("PRAGMA table_info(characters)")
    columns = [col[1] for col in cur.fetchall()]
    
    if 'vip' not in columns:
        conn.close()
        return 0, None
    
    cur.execute('SELECT vip, vip_expires_at FROM characters WHERE id = ?', (character_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        vip_level = row[0] or 0
        expires_at = row[1]
        if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
            return 0, None
        return vip_level, expires_at
    return 0, None


def set_vip(character_id, vip_level, days=30):
    """Установка VIP-статуса"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    expires_at = datetime.now() + timedelta(days=days)
    cur.execute('''
        UPDATE characters 
        SET vip = ?, vip_expires_at = ?
        WHERE id = ?
    ''', (vip_level, expires_at.isoformat(), character_id))
    conn.commit()
    conn.close()
    return True


def remove_vip(character_id):
    """Снятие VIP-статуса"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE characters SET vip = 0, vip_expires_at = NULL WHERE id = ?', (character_id,))
    conn.commit()
    conn.close()
    return True


def get_vip_bonus(vip_level):
    """Получение бонусов VIP"""
    return VIP_BONUSES.get(vip_level, {'exp': 0, 'silver': 0})


def format_vip_name(character_id, name):
    """Форматирование имени с VIP-статусом"""
    vip_level, _ = get_vip(character_id)
    if vip_level > 0:
        vip_name = VIP_NAMES.get(vip_level, '')
        vip_icon = VIP_COLORS.get(vip_level, '')
        return f"{vip_icon}[{vip_name}] {name}"
    return name


def get_vip_icon(vip_level):
    """Получение иконки VIP"""
    return VIP_COLORS.get(vip_level, '')


def get_vip_name(vip_level):
    """Получение названия VIP"""
    return VIP_NAMES.get(vip_level, '')


def format_vip_profile(char):
    """Форматирование профиля с VIP-статусом"""
    vip_level, expires_at = get_vip(char['id'])
    if vip_level > 0:
        vip_icon = VIP_COLORS.get(vip_level, '')
        vip_name = VIP_NAMES.get(vip_level, '')
        bonus = VIP_BONUSES.get(vip_level, {})
        
        # Считаем оставшееся время
        if expires_at:
            remaining = datetime.fromisoformat(expires_at) - datetime.now()
            days = remaining.days
            if days > 0:
                time_text = f"{days} дн."
            else:
                hours = remaining.seconds // 3600
                time_text = f"{hours} ч." if hours > 0 else "менее часа"
        else:
            time_text = "неизвестно"
        
        return {
            'icon': vip_icon,
            'name': vip_name,
            'bonus': bonus,
            'time': time_text
        }
    return None