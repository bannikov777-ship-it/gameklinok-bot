# quests.py
import sqlite3
import traceback
from config import DB_NAME
from datetime import datetime

def seed_hunter_quests():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM hunter_quest_templates')
    if cur.fetchone()[0] == 0:
        cur.execute('SELECT id FROM consumable_templates WHERE restore_percent = 25 AND restore_type = "hp"')
        row = cur.fetchone()
        potion_template_id = row[0] if row else None
        quests = [
            ('Истребление гоблинов', 'Убейте 10 Гоблинов-разведчиков', 10, 'Гоблин-разведчик', 150, 3, potion_template_id),
            ('Охота на волков', 'Убейте 8 Волков-одиночек', 8, 'Волк-одиночка', 120, 2, potion_template_id),
            ('Чистка леса', 'Убейте 5 Лесных троллей', 5, 'Лесной тролль', 200, 4, potion_template_id),
            ('Уничтожение нежити', 'Убейте 5 Зомби-лесников', 5, 'Зомби-лесник', 100, 2, potion_template_id),
            ('Очистка кладбища', 'Убейте 10 Скелетов-воинов', 10, 'Скелет-воин', 180, 3, potion_template_id),
            ('Охота на нежить', 'Убейте 8 Зомби-могильщиков', 8, 'Зомби-могильщик', 150, 2, potion_template_id),
            ('Изгнание призраков', 'Убейте 5 Призраков-странников', 5, 'Призрак-странник', 200, 4, potion_template_id),
            ('Битва с рыцарями', 'Убейте 5 Рыцарей-мертвецов', 5, 'Рыцарь-мертвец', 250, 5, potion_template_id),
        ]
        cur.executemany('''
            INSERT INTO hunter_quest_templates (name, description, target_count, monster_name, reward_silver, reward_potion_count, reward_potion_template_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', quests)
        conn.commit()
    conn.close()

def get_available_quests(player_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT quest_template_id FROM player_quests WHERE player_id = ? AND completed = 0', (player_id,))
    active = [row[0] for row in cur.fetchall()]
    cur.execute('SELECT id, name, description, target_count, reward_silver, reward_potion_count FROM hunter_quest_templates')
    all_quests = cur.fetchall()
    conn.close()
    available = []
    for q in all_quests:
        if q[0] not in active:
            available.append({
                'id': q[0],
                'name': q[1],
                'description': q[2],
                'target_count': q[3],
                'reward_silver': q[4],
                'reward_potion_count': q[5]
            })
    return available

def take_quest(player_id, quest_template_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM player_quests WHERE player_id = ? AND completed = 0', (player_id,))
    active_count = cur.fetchone()[0]
    if active_count >= 3:
        conn.close()
        return False, "У вас уже 3 активных задания."
    today = datetime.now().strftime('%Y-%m-%d')
    cur.execute('''INSERT INTO daily_quest_stats (player_id, date, completed_today) 
                   VALUES (?, ?, 0) ON CONFLICT(player_id) DO UPDATE SET date = excluded.date''', (player_id, today))
    cur.execute('SELECT completed_today FROM daily_quest_stats WHERE player_id = ?', (player_id,))
    completed_today = cur.fetchone()[0]
    if completed_today >= 3:
        conn.close()
        return False, "Вы уже выполнили 3 задания сегодня. Приходите завтра."
    cur.execute('SELECT id FROM player_quests WHERE player_id = ? AND quest_template_id = ? AND completed = 0', (player_id, quest_template_id))
    if cur.fetchone():
        conn.close()
        return False, "Вы уже взяли это задание."
    cur.execute('INSERT INTO player_quests (player_id, quest_template_id, progress) VALUES (?, ?, 0)', (player_id, quest_template_id))
    conn.commit()
    conn.close()
    return True, "Задание взято!"

def get_active_quests(player_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT pq.id, qt.name, qt.description, qt.target_count, pq.progress, qt.reward_silver, qt.reward_potion_count
        FROM player_quests pq JOIN hunter_quest_templates qt ON pq.quest_template_id = qt.id
        WHERE pq.player_id = ? AND pq.completed = 0
    ''', (player_id,))
    rows = cur.fetchall()
    conn.close()
    quests = []
    for row in rows:
        quests.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'target': row[3],
            'progress': row[4],
            'reward_silver': row[5],
            'reward_potion_count': row[6]
        })
    return quests

def update_quest_progress(player_id, monster_name=None, monster_killed=1):
    print(f"📌 update_quest_progress: player_id={player_id}, monster_name={monster_name}, monster_killed={monster_killed}")
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('''
            SELECT pq.id, qt.target_count, qt.reward_silver, qt.reward_potion_count, qt.reward_potion_template_id, qt.monster_name
            FROM player_quests pq JOIN hunter_quest_templates qt ON pq.quest_template_id = qt.id
            WHERE pq.player_id = ? AND pq.completed = 0
        ''', (player_id,))
        quests = cur.fetchall()
        print(f"📋 Найдено активных квестов: {len(quests)}")
        if not quests:
            print("ℹ️ Нет активных квестов для обновления.")
            conn.close()
            return False
        completed_any = False
        for q in quests:
            q_id, target, reward_silver, potion_count, potion_template_id, quest_monster = q
            print(f"🔍 Проверяем квест ID={q_id}, требуется монстр: {quest_monster}")
            if quest_monster and monster_name and quest_monster != monster_name:
                print(f"   ⏭️ Пропускаем: монстр {monster_name} не соответствует {quest_monster}")
                continue
            print(f"   ✅ Подходит! Увеличиваем прогресс на {monster_killed}")
            cur.execute('UPDATE player_quests SET progress = progress + ? WHERE id = ?', (monster_killed, q_id))
            cur.execute('SELECT progress FROM player_quests WHERE id = ?', (q_id,))
            progress = cur.fetchone()[0]
            print(f"   📊 Новый прогресс: {progress}/{target}")
            if progress >= target:
                print(f"   🎉 Квест выполнен! ID={q_id}")
                cur.execute('UPDATE player_quests SET completed = 1 WHERE id = ?', (q_id,))
                completed_any = True
                cur.execute('UPDATE characters SET silver = silver + ? WHERE id = ?', (reward_silver, player_id))
                if potion_template_id:
                    cur.execute('INSERT INTO player_consumables (owner_id, consumable_template_id, quantity) VALUES (?, ?, ?) '
                                'ON CONFLICT(owner_id, consumable_template_id) DO UPDATE SET quantity = quantity + ?',
                                (player_id, potion_template_id, potion_count, potion_count))
                cur.execute('UPDATE daily_quest_stats SET completed_today = completed_today + 1 WHERE player_id = ?', (player_id,))
        conn.commit()
        conn.close()
        print(f"✅ update_quest_progress завершён, completed_any={completed_any}")
        return completed_any
    except Exception as e:
        print(f"⚠️ Ошибка обновления прогресса квеста: {e}")
        traceback.print_exc()
        return False

def get_completed_quests_count_today(player_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    cur.execute('''INSERT INTO daily_quest_stats (player_id, date, completed_today) 
                   VALUES (?, ?, 0) ON CONFLICT(player_id) DO UPDATE SET date = excluded.date''', (player_id, today))
    cur.execute('SELECT completed_today FROM daily_quest_stats WHERE player_id = ?', (player_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count