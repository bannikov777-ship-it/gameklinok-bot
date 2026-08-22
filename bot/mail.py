# mail.py
import sqlite3
from config import DB_NAME

def get_unread_mail_count(character_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM mail WHERE recipient_id = ? AND is_read = 0', (character_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count

def send_mail_with_attachment(sender_id, recipient_name, subject, body, attachment_type=None, attachment_id=None, attachment_quantity=1, attachment_silver=0):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM characters WHERE name = ?', (recipient_name,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Игрок с таким именем не найден."
    recipient_id = row[0]
    if recipient_id == sender_id:
        conn.close()
        return False, "Нельзя отправить письмо самому себе."
    if attachment_type == 'item':
        cur.execute('SELECT id, quantity FROM player_items WHERE id = ? AND owner_id = ?', (attachment_id, sender_id))
        item_row = cur.fetchone()
        if not item_row:
            conn.close()
            return False, "У вас нет такого предмета."
        if item_row[1] < attachment_quantity:
            conn.close()
            return False, "Недостаточно предметов."
        if item_row[1] == attachment_quantity:
            cur.execute('DELETE FROM player_items WHERE id = ?', (attachment_id,))
        else:
            cur.execute('UPDATE player_items SET quantity = quantity - ? WHERE id = ?', (attachment_quantity, attachment_id))
    elif attachment_type == 'consumable':
        cur.execute('SELECT id, quantity FROM player_consumables WHERE id = ? AND owner_id = ?', (attachment_id, sender_id))
        cons_row = cur.fetchone()
        if not cons_row:
            conn.close()
            return False, "У вас нет такого расходника."
        if cons_row[1] < attachment_quantity:
            conn.close()
            return False, "Недостаточно расходников."
        if cons_row[1] == attachment_quantity:
            cur.execute('DELETE FROM player_consumables WHERE id = ?', (attachment_id,))
        else:
            cur.execute('UPDATE player_consumables SET quantity = quantity - ? WHERE id = ?', (attachment_quantity, attachment_id))
    elif attachment_type == 'money':
        cur.execute('SELECT silver FROM characters WHERE id = ?', (sender_id,))
        silver = cur.fetchone()[0]
        if silver < attachment_silver:
            conn.close()
            return False, "Недостаточно серебра."
        cur.execute('UPDATE characters SET silver = silver - ? WHERE id = ?', (attachment_silver, sender_id))
    cur.execute('''
        INSERT INTO mail (recipient_id, sender_id, subject, body, attachment_type, attachment_id, attachment_quantity, attachment_silver)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (recipient_id, sender_id, subject, body, attachment_type, attachment_id, attachment_quantity, attachment_silver))
    conn.commit()
    conn.close()
    return True, "Письмо с вложением отправлено!"

def get_mail(character_id, only_unread=False):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if only_unread:
        cur.execute('''
            SELECT m.id, m.subject, m.body, m.is_read, m.created_at, c.name as sender_name,
                   m.attachment_type, m.attachment_id, m.attachment_quantity, m.attachment_silver
            FROM mail m
            JOIN characters c ON m.sender_id = c.id
            WHERE m.recipient_id = ? AND m.is_read = 0
            ORDER BY m.created_at DESC
        ''', (character_id,))
    else:
        cur.execute('''
            SELECT m.id, m.subject, m.body, m.is_read, m.created_at, c.name as sender_name,
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
            'attachment_type': row[6],
            'attachment_id': row[7],
            'attachment_quantity': row[8] or 0,
            'attachment_silver': row[9] or 0
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
    cur.execute('SELECT attachment_type, attachment_id, attachment_quantity, attachment_silver FROM mail WHERE id = ? AND recipient_id = ? AND is_read = 1', (mail_id, character_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Письмо не найдено или не прочитано."
    attachment_type, attachment_id, quantity, silver = row
    if not attachment_type:
        conn.close()
        return False, "В этом письме нет вложения."
    cur.execute('UPDATE mail SET attachment_type = NULL, attachment_id = NULL, attachment_quantity = 0, attachment_silver = 0 WHERE id = ?', (mail_id,))
    if attachment_type == 'item':
        cur.execute('SELECT template_id, level, rarity, upgrade_level FROM player_items WHERE id = ?', (attachment_id,))
        item_data = cur.fetchone()
        if item_data:
            template_id, level, rarity, upgrade_level = item_data
            cur.execute('INSERT INTO player_items (owner_id, template_id, level, rarity, upgrade_level, quantity) VALUES (?, ?, ?, ?, ?, ?)',
                        (character_id, template_id, level, rarity, upgrade_level, quantity))
    elif attachment_type == 'consumable':
        cur.execute('SELECT consumable_template_id FROM player_consumables WHERE id = ?', (attachment_id,))
        template_id = cur.fetchone()[0]
        cur.execute('INSERT INTO player_consumables (owner_id, consumable_template_id, quantity) VALUES (?, ?, ?) '
                    'ON CONFLICT(owner_id, consumable_template_id) DO UPDATE SET quantity = quantity + ?',
                    (character_id, template_id, quantity, quantity))
    elif attachment_type == 'money':
        cur.execute('UPDATE characters SET silver = silver + ? WHERE id = ?', (silver, character_id))
    conn.commit()
    conn.close()
    return True, "Вложение получено!"