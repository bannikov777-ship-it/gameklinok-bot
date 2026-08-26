# mail.py (полный исправленный файл)
import sqlite3
import json
from config import DB_NAME

def get_unread_mail_count(character_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM mail WHERE recipient_id = ? AND is_read = 0', (character_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count


def send_mail_with_attachment_by_id(sender_id, recipient_id, subject, body, 
                                     attachment_type=None, attachment_id=None, 
                                     attachment_quantity=1, attachment_silver=0):
    """Отправка письма с вложением по ID получателя"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Проверяем, существует ли получатель
    cur.execute('SELECT id FROM characters WHERE id = ?', (recipient_id,))
    if not cur.fetchone():
        conn.close()
        return False, "Игрок с таким ID не найден."
    
    if recipient_id == sender_id:
        conn.close()
        return False, "Нельзя отправить письмо самому себе."
    
    # Получаем имя отправителя для проверки
    cur.execute('SELECT name FROM characters WHERE id = ?', (sender_id,))
    sender_row = cur.fetchone()
    if not sender_row:
        conn.close()
        return False, "Отправитель не найден."
    
    # Обработка вложения
    if attachment_type == 'item':
        if not attachment_id:
            conn.close()
            return False, "Не указан ID предмета."
        
        # Получаем ВСЕ данные предмета перед удалением
        cur.execute('SELECT template_id, level, rarity, upgrade_level, quantity FROM player_items WHERE id = ? AND owner_id = ?', 
                   (attachment_id, sender_id))
        item_row = cur.fetchone()
        if not item_row:
            conn.close()
            return False, "У вас нет такого предмета."
        
        template_id, level, rarity, upgrade_level, quantity = item_row
        if quantity < attachment_quantity:
            conn.close()
            return False, "Недостаточно предметов."
        
        # Удаляем или уменьшаем количество у отправителя
        if quantity == attachment_quantity:
            cur.execute('DELETE FROM player_items WHERE id = ?', (attachment_id,))
        else:
            cur.execute('UPDATE player_items SET quantity = quantity - ? WHERE id = ?', 
                       (attachment_quantity, attachment_id))
        
        # Сохраняем данные предмета в JSON
        extra_data = {
            'level': level,
            'rarity': rarity,
            'upgrade_level': upgrade_level
        }
        silver_extra = json.dumps(extra_data)
        
        # Создаём письмо с сохранёнными данными (attachment_id = template_id)
        cur.execute('''
            INSERT INTO mail (recipient_id, sender_id, subject, body, 
                              attachment_type, attachment_id, 
                              attachment_quantity, attachment_silver)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (recipient_id, sender_id, subject, body, 
              attachment_type, template_id, attachment_quantity, silver_extra))
              
    elif attachment_type == 'consumable':
        if not attachment_id:
            conn.close()
            return False, "Не указан ID расходника."
        cur.execute('SELECT consumable_template_id, quantity FROM player_consumables WHERE id = ? AND owner_id = ?', 
                   (attachment_id, sender_id))
        cons_row = cur.fetchone()
        if not cons_row:
            conn.close()
            return False, "У вас нет такого расходника."
        template_id, quantity = cons_row
        if quantity < attachment_quantity:
            conn.close()
            return False, "Недостаточно расходников."
        if quantity == attachment_quantity:
            cur.execute('DELETE FROM player_consumables WHERE id = ?', (attachment_id,))
        else:
            cur.execute('UPDATE player_consumables SET quantity = quantity - ? WHERE id = ?', 
                       (attachment_quantity, attachment_id))
        
        # Создаём письмо (attachment_id = template_id)
        cur.execute('''
            INSERT INTO mail (recipient_id, sender_id, subject, body, 
                              attachment_type, attachment_id, 
                              attachment_quantity, attachment_silver)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (recipient_id, sender_id, subject, body, 
              attachment_type, template_id, attachment_quantity, 0))
            
    elif attachment_type == 'money':
        if attachment_silver <= 0:
            conn.close()
            return False, "Сумма должна быть положительной."
        cur.execute('SELECT silver FROM characters WHERE id = ?', (sender_id,))
        silver_row = cur.fetchone()
        if not silver_row:
            conn.close()
            return False, "Отправитель не найден."
        silver = silver_row[0]
        if silver < attachment_silver:
            conn.close()
            return False, "Недостаточно серебра."
        cur.execute('UPDATE characters SET silver = silver - ? WHERE id = ?', 
                   (attachment_silver, sender_id))
        
        cur.execute('''
            INSERT INTO mail (recipient_id, sender_id, subject, body, 
                              attachment_type, attachment_id, 
                              attachment_quantity, attachment_silver)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (recipient_id, sender_id, subject, body, 
              attachment_type, None, 0, attachment_silver))
    
    else:
        # Без вложения
        cur.execute('''
            INSERT INTO mail (recipient_id, sender_id, subject, body, 
                              attachment_type, attachment_id, 
                              attachment_quantity, attachment_silver)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (recipient_id, sender_id, subject, body, 
              None, None, 0, 0))
    
    conn.commit()
    conn.close()
    return True, "Письмо с вложением отправлено!"


def send_mail_with_attachment(sender_id, recipient_name, subject, body, 
                               attachment_type=None, attachment_id=None, 
                               attachment_quantity=1, attachment_silver=0):
    """Отправка письма с вложением по имени (устаревший метод, оставлен для совместимости)"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM characters WHERE name = ?', (recipient_name,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Игрок с таким именем не найден."
    recipient_id = row[0]
    conn.close()
    return send_mail_with_attachment_by_id(sender_id, recipient_id, subject, body,
                                          attachment_type, attachment_id, 
                                          attachment_quantity, attachment_silver)


def get_mail(character_id, only_unread=False):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if only_unread:
        cur.execute('''
            SELECT m.id, m.subject, m.body, m.is_read, m.created_at, 
                   c.name as sender_name, c.id as sender_id,
                   m.attachment_type, m.attachment_id, m.attachment_quantity, m.attachment_silver
            FROM mail m
            JOIN characters c ON m.sender_id = c.id
            WHERE m.recipient_id = ? AND m.is_read = 0
            ORDER BY m.created_at DESC
        ''', (character_id,))
    else:
        cur.execute('''
            SELECT m.id, m.subject, m.body, m.is_read, m.created_at, 
                   c.name as sender_name, c.id as sender_id,
                   m.attachment_type, m.attachment_id, m.attachment_quantity, m.attachment_silver
            FROM mail m
            JOIN characters c ON m.sender_id = c.id
            WHERE m.recipient_id = ?
            ORDER BY m.created_at DESC
        ''', (character_id,))
    rows = cur.fetchall()
    conn.close()
    mail_list = []
    for row in rows:
        mail_list.append({
            'id': row[0],
            'subject': row[1],
            'body': row[2],
            'is_read': row[3],
            'created_at': row[4],
            'sender_name': row[5],
            'sender_id': row[6],
            'attachment_type': row[7],
            'attachment_id': row[8],
            'attachment_quantity': row[9] or 0,
            'attachment_silver': row[10] or 0
        })
    return mail_list


def mark_mail_as_read(mail_id, character_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE mail SET is_read = 1 WHERE id = ? AND recipient_id = ?', (mail_id, character_id))
    conn.commit()
    conn.close()


def delete_mail(mail_id, character_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('DELETE FROM mail WHERE id = ? AND recipient_id = ?', (mail_id, character_id))
    conn.commit()
    conn.close()


def claim_attachment(mail_id, character_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT attachment_type, attachment_id, attachment_quantity, attachment_silver FROM mail WHERE id = ? AND recipient_id = ? AND is_read = 1', 
                (mail_id, character_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Письмо не найдено или не прочитано."
    
    attachment_type, attachment_id, quantity, silver = row
    if not attachment_type:
        conn.close()
        return False, "В этом письме нет вложения."
    
    # Помечаем, что вложение забрано
    cur.execute('UPDATE mail SET attachment_type = NULL, attachment_id = NULL, attachment_quantity = 0, attachment_silver = 0 WHERE id = ?', (mail_id,))
    
    if attachment_type == 'item':
        # Для предметов: attachment_id = template_id, attachment_silver = JSON с данными
        try:
            extra_data = json.loads(silver) if silver else {}
        except:
            extra_data = {}
        
        template_id = attachment_id
        level = extra_data.get('level', 1)
        rarity = extra_data.get('rarity', 1)
        upgrade_level = extra_data.get('upgrade_level', 0)
        
        # Проверяем, существует ли такой template_id
        cur.execute('SELECT id FROM item_templates WHERE id = ?', (template_id,))
        if not cur.fetchone():
            conn.close()
            return False, "Шаблон предмета не найден."
        
        # Создаём предмет для получателя
        cur.execute('''
            INSERT INTO player_items (owner_id, template_id, level, rarity, upgrade_level, quantity) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (character_id, template_id, level, rarity, upgrade_level, quantity))
        
    elif attachment_type == 'consumable':
        # Для расходников: attachment_id = consumable_template_id
        template_id = attachment_id
        cur.execute('SELECT id FROM consumable_templates WHERE id = ?', (template_id,))
        if not cur.fetchone():
            conn.close()
            return False, "Шаблон расходника не найден."
        
        cur.execute('''
            INSERT INTO player_consumables (owner_id, consumable_template_id, quantity) 
            VALUES (?, ?, ?) 
            ON CONFLICT(owner_id, consumable_template_id) DO UPDATE SET quantity = quantity + ?
        ''', (character_id, template_id, quantity, quantity))
            
    elif attachment_type == 'money':
        cur.execute('UPDATE characters SET silver = silver + ? WHERE id = ?', (silver, character_id))
    
    conn.commit()
    conn.close()
    return True, "Вложение получено!"