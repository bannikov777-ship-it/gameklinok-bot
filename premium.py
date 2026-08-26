# premium.py
import sqlite3
import json
from config import DB_NAME
from core import get_character_by_id, update_user_async

def get_premium_shop_items():
    """Получение всех товаров из премиум-магазина"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, name, description, icon, price, item_type, item_data FROM premium_shop')
    rows = cur.fetchall()
    conn.close()
    
    items = []
    for row in rows:
        items.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'icon': row[3],
            'price': row[4],
            'item_type': row[5],
            'item_data': json.loads(row[6]) if row[6] else {}
        })
    return items


def buy_premium_item(character_id, item_id):
    """Покупка предмета в премиум-магазине"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute('SELECT name, price, item_type, item_data FROM premium_shop WHERE id = ?', (item_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Товар не найден."
    
    name, price, item_type, item_data_json = row
    item_data = json.loads(item_data_json) if item_data_json else {}
    
    cur.execute('SELECT crystals FROM characters WHERE id = ?', (character_id,))
    crystals_row = cur.fetchone()
    if not crystals_row or crystals_row[0] < price:
        conn.close()
        return False, f"Недостаточно кристаллов! Нужно {price}💎."
    
    # Проверка VIP перед покупкой
    if item_type == 'vip':
        vip_level = item_data.get('vip_level', 1)
        cur.execute('SELECT vip FROM characters WHERE id = ?', (character_id,))
        current_vip = cur.fetchone()[0] or 0
        
        if current_vip > 0 and current_vip != vip_level:
            conn.close()
            vip_names = {1: 'Бронзовый', 2: 'Серебряный', 3: 'Золотой', 4: 'Платиновый', 5: 'Алмазный'}
            return False, f"❌ У вас уже есть VIP {vip_names.get(current_vip, '')}. Нельзя купить VIP другого уровня. Только продление текущего."
    
    cur.execute('UPDATE characters SET crystals = crystals - ? WHERE id = ?', (price, character_id))
    
    result = give_premium_reward(conn, cur, character_id, item_type, item_data)
    if not result[0]:
        conn.rollback()
        conn.close()
        return False, result[1]
    
    conn.commit()
    conn.close()
    return True, f"✅ Вы купили {name}!"


def give_premium_reward(conn, cur, character_id, item_type, item_data):
    """Выдача награды из премиум-магазина"""
    
    if item_type == 'crystal_pack':
        crystal_type = item_data.get('crystal_type')
        count = item_data.get('count', 1)
        
        crystal_map = {
            'weak': 10,    # Голубой кристалл (+15%)
            'medium': 11,  # Фиолетовый кристалл (35%)
            'strong': 12   # Красный кристалл (+55%)
        }
        
        template_id = crystal_map.get(crystal_type)
        if not template_id:
            return False, "Неизвестный тип кристалла."
        
        cur.execute('''
            INSERT INTO player_consumables (owner_id, consumable_template_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(owner_id, consumable_template_id) DO UPDATE SET quantity = quantity + ?
        ''', (character_id, template_id, count, count))
        
        return True, f"Получено {count} кристаллов!"
    
    elif item_type == 'scroll':
        effect = item_data.get('effect')
        if effect == 'remove_curse':
            # Ищем свиток в consumable_templates
            cur.execute('SELECT id FROM consumable_templates WHERE restore_type = "curse_remove"')
            scroll_row = cur.fetchone()
            
            if not scroll_row:
                # Если свитка нет, создаём
                cur.execute('''
                    INSERT INTO consumable_templates (name, description, icon, restore_type, restore_percent, price)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ('Свиток снятия проклятия', 'Снимает любое проклятие', '📜', 'curse_remove', 0, 0))
                conn.commit()
                cur.execute('SELECT id FROM consumable_templates WHERE restore_type = "curse_remove"')
                scroll_row = cur.fetchone()
            
            scroll_id = scroll_row[0]
            print(f"📜 Добавляем свиток с ID: {scroll_id}")
            
            # Добавляем свиток в инвентарь игрока
            cur.execute('''
                INSERT INTO player_consumables (owner_id, consumable_template_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(owner_id, consumable_template_id) DO UPDATE SET quantity = quantity + ?
            ''', (character_id, scroll_id, 1, 1))
            
            return True, "Свиток снятия проклятия получен!"
        return False, "Неизвестный эффект свитка."
    
    elif item_type == 'vip':
        vip_level = item_data.get('vip_level', 1)
        bonus = item_data.get('bonus', 20)
        
        from datetime import datetime, timedelta
        
        cur.execute('SELECT vip, vip_expires_at FROM characters WHERE id = ?', (character_id,))
        vip_row = cur.fetchone()
        
        if vip_row and vip_row[0] > 0:
            expires_at = datetime.fromisoformat(vip_row[1]) if vip_row[1] else datetime.now()
            if expires_at < datetime.now():
                expires_at = datetime.now()
            new_expires = expires_at + timedelta(days=30)
        else:
            new_expires = datetime.now() + timedelta(days=30)
        
        cur.execute('''
            UPDATE characters 
            SET vip = ?, vip_expires_at = ?
            WHERE id = ?
        ''', (vip_level, new_expires.isoformat(), character_id))
        
        return True, f"VIP {bonus}% выдан на 30 дней!"
    
    return False, "Неизвестный тип товара."