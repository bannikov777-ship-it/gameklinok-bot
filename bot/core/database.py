# core/database.py (полный исправленный)
import sqlite3
import json
from config import DB_NAME

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('PRAGMA journal_mode=WAL')
    cur.execute('PRAGMA busy_timeout=5000')
    cur.execute('PRAGMA synchronous=NORMAL')
    
    # users
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            vk_id INTEGER PRIMARY KEY,
            state TEXT DEFAULT 'city',
            context TEXT DEFAULT '{}'
        )
    ''')
    
    # characters
    cur.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vk_id INTEGER UNIQUE,
            name TEXT,
            gender TEXT,
            class TEXT,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            silver INTEGER DEFAULT 50,
            crystals INTEGER DEFAULT 0,
            attack INTEGER DEFAULT 10,
            defense INTEGER DEFAULT 2,
            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            mana INTEGER DEFAULT 20,
            max_mana INTEGER DEFAULT 20,
            stamina INTEGER DEFAULT 50,
            max_stamina INTEGER DEFAULT 50,
            crit_chance INTEGER DEFAULT 5,
            dodge_chance INTEGER DEFAULT 5,
            debuff INTEGER DEFAULT 0,
            max_forest_depth INTEGER DEFAULT 0,
            current_city INTEGER DEFAULT 1,
            trophies INTEGER DEFAULT 0,
            materials TEXT DEFAULT '{}',
            guild_exp_contributed INTEGER DEFAULT 0,
            guild_quests_completed INTEGER DEFAULT 0,
            vip INTEGER DEFAULT 0,
            vip_expires_at TIMESTAMP DEFAULT NULL
        )
    ''')
    
    # cities
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            image_attachment TEXT
        )
    ''')
    
    # consumable_templates
    cur.execute('''
        CREATE TABLE IF NOT EXISTS consumable_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            icon TEXT,
            restore_type TEXT,
            restore_percent INTEGER,
            price INTEGER
        )
    ''')
    
    # player_consumables
    cur.execute('''
        CREATE TABLE IF NOT EXISTS player_consumables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            consumable_template_id INTEGER,
            quantity INTEGER DEFAULT 0,
            UNIQUE(owner_id, consumable_template_id)
        )
    ''')
    
    # guilds
    cur.execute('''
        CREATE TABLE IF NOT EXISTS guilds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            leader_id INTEGER UNIQUE,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            silver INTEGER DEFAULT 0,
            max_members INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # guild_members
    cur.execute('''
        CREATE TABLE IF NOT EXISTS guild_members (
            guild_id INTEGER,
            character_id INTEGER,
            rank TEXT DEFAULT 'Участник',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (guild_id, character_id)
        )
    ''')
    
    # guild_storage
    cur.execute('''
        CREATE TABLE IF NOT EXISTS guild_storage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            template_id INTEGER,
            level INTEGER DEFAULT 1,
            rarity INTEGER DEFAULT 1,
            upgrade_level INTEGER DEFAULT 0,
            quantity INTEGER DEFAULT 1,
            item_type TEXT DEFAULT 'item',
            name TEXT DEFAULT 'Неизвестный предмет'
        )
    ''')
    
    # guild_applications
    cur.execute('''
        CREATE TABLE IF NOT EXISTS guild_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            reviewed_by INTEGER,
            FOREIGN KEY (guild_id) REFERENCES guilds(id),
            FOREIGN KEY (player_id) REFERENCES characters(id),
            FOREIGN KEY (reviewed_by) REFERENCES characters(id)
        )
    ''')
    
    # auction_lots
    cur.execute('''
        CREATE TABLE IF NOT EXISTS auction_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_type TEXT NOT NULL,
            seller_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_id INTEGER,
            template_id INTEGER,
            level INTEGER DEFAULT 1,
            rarity INTEGER DEFAULT 1,
            upgrade_level INTEGER DEFAULT 0,
            quantity INTEGER DEFAULT 1,
            price INTEGER NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP DEFAULT (datetime('now', '+24 hours'))
        )
    ''')
    
    # hunter_quest_templates
    cur.execute('''
        CREATE TABLE IF NOT EXISTS hunter_quest_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            target_count INTEGER,
            monster_name TEXT,
            reward_silver INTEGER,
            reward_potion_count INTEGER,
            reward_potion_template_id INTEGER
        )
    ''')
    
    # player_quests
    cur.execute('''
        CREATE TABLE IF NOT EXISTS player_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            quest_template_id INTEGER,
            progress INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # daily_quest_stats
    cur.execute('''
        CREATE TABLE IF NOT EXISTS daily_quest_stats (
            player_id INTEGER PRIMARY KEY,
            date TEXT,
            completed_today INTEGER DEFAULT 0
        )
    ''')
    
    # tower_party
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tower_party (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            leader_id INTEGER UNIQUE,
            members TEXT DEFAULT '[]',
            current_floor INTEGER DEFAULT 1,
            current_boss TEXT DEFAULT '{}',
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # tower_bosses
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tower_bosses (
            floor INTEGER PRIMARY KEY,
            name TEXT,
            base_hp INTEGER,
            base_attack INTEGER,
            base_defense INTEGER,
            exp_reward INTEGER,
            silver_reward INTEGER
        )
    ''')
    
    # tower_invites
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tower_invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            party_id INTEGER,
            invited_id INTEGER,
            leader_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    # mail
    cur.execute('''
        CREATE TABLE IF NOT EXISTS mail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_id INTEGER,
            sender_id INTEGER,
            subject TEXT,
            body TEXT,
            is_read INTEGER DEFAULT 0,
            attachment_type TEXT DEFAULT NULL,
            attachment_id INTEGER DEFAULT NULL,
            attachment_quantity INTEGER DEFAULT 0,
            attachment_silver INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # resource_templates
    cur.execute('''
        CREATE TABLE IF NOT EXISTS resource_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            icon TEXT,
            zone TEXT,
            rarity INTEGER DEFAULT 1,
            price INTEGER DEFAULT 10,
            description TEXT
        )
    ''')
    
    # player_resources
    cur.execute('''
        CREATE TABLE IF NOT EXISTS player_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            resource_id INTEGER,
            quantity INTEGER DEFAULT 0,
            UNIQUE(owner_id, resource_id)
        )
    ''')
    
    # craft_recipes
    cur.execute('''
        CREATE TABLE IF NOT EXISTS craft_recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_type TEXT,
            result_id INTEGER,
            result_quantity INTEGER DEFAULT 1,
            ingredient1_type TEXT,
            ingredient1_id INTEGER,
            ingredient1_quantity INTEGER,
            ingredient2_type TEXT,
            ingredient2_id INTEGER,
            ingredient2_quantity INTEGER,
            ingredient3_type TEXT,
            ingredient3_id INTEGER,
            ingredient3_quantity INTEGER
        )
    ''')
    
    # herbs
    cur.execute('''
        CREATE TABLE IF NOT EXISTS herbs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            icon TEXT,
            price INTEGER,
            description TEXT
        )
    ''')
    
    # player_herbs
    cur.execute('''
        CREATE TABLE IF NOT EXISTS player_herbs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            herb_id INTEGER,
            quantity INTEGER DEFAULT 0,
            UNIQUE(owner_id, herb_id)
        )
    ''')
    
    # guild_quests
    cur.execute('''
        CREATE TABLE IF NOT EXISTS guild_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            duration_minutes INTEGER,
            exp_reward INTEGER,
            silver_reward INTEGER,
            extra_reward_type TEXT,
            extra_reward_id INTEGER,
            extra_reward_quantity INTEGER DEFAULT 1,
            extra_reward_rarity INTEGER DEFAULT 1
        )
    ''')
    
    # player_guild_quests
    cur.execute('''
        CREATE TABLE IF NOT EXISTS player_guild_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            quest_id INTEGER,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            completed INTEGER DEFAULT 0,
            rewarded INTEGER DEFAULT 0,
            FOREIGN KEY (player_id) REFERENCES characters(id),
            FOREIGN KEY (quest_id) REFERENCES guild_quests(id)
        )
    ''')
    
    # guild_quests_daily
    cur.execute('''
        CREATE TABLE IF NOT EXISTS guild_quests_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            date TEXT,
            quests TEXT DEFAULT '[]',
            UNIQUE(guild_id, date)
        )
    ''')
    
    # item_templates
    cur.execute('''
        CREATE TABLE IF NOT EXISTS item_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            slot TEXT,
            base_attack INTEGER DEFAULT 0,
            base_defense INTEGER DEFAULT 0,
            base_hp INTEGER DEFAULT 0,
            base_mana INTEGER DEFAULT 0,
            growth_attack REAL DEFAULT 0.1,
            growth_defense REAL DEFAULT 0.1,
            growth_hp REAL DEFAULT 0.1,
            growth_mana REAL DEFAULT 0.1,
            icon TEXT DEFAULT '🗡️',
            bonus_crit INTEGER DEFAULT 0,
            bonus_dodge INTEGER DEFAULT 0
        )
    ''')
    
    # player_items
    cur.execute('''
        CREATE TABLE IF NOT EXISTS player_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            template_id INTEGER,
            level INTEGER DEFAULT 1,
            rarity INTEGER DEFAULT 1,
            upgrade_level INTEGER DEFAULT 0,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (owner_id) REFERENCES characters(id),
            FOREIGN KEY (template_id) REFERENCES item_templates(id)
        )
    ''')
    
    # premium_shop
    cur.execute('''
        CREATE TABLE IF NOT EXISTS premium_shop (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            icon TEXT,
            price INTEGER,
            item_type TEXT,
            item_data TEXT
        )
    ''')
    
    # ✅ Исправлено: equipment создаётся только если не существует
    cur.execute('''
        CREATE TABLE IF NOT EXISTS equipment (
            character_id INTEGER,
            slot TEXT,
            player_item_id INTEGER,
            PRIMARY KEY (character_id, slot),
            FOREIGN KEY (character_id) REFERENCES characters(id),
            FOREIGN KEY (player_item_id) REFERENCES player_items(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")


def seed_cities():
    """Заполнение городов"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM cities')
    if cur.fetchone()[0] == 0:
        cities = [
            (1, 'Стальной Трон', 'Небольшой город у подножия холмов...', 'photo-240828623_456239028'),
            (2, 'Озерный Край', 'Город, раскинувшийся на берегу большого озера...', 'photo-240828623_456239022')
        ]
        cur.executemany('INSERT INTO cities (id, name, description, image_attachment) VALUES (?, ?, ?, ?)', cities)
        conn.commit()
    conn.close()


def seed_consumables():
    """Заполнение расходников"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM consumable_templates')
    if cur.fetchone()[0] == 0:
        consumables = [
            ('Слабое зелье здоровья', 'Восстанавливает 10% HP', '❤️', 'hp', 10, 20),
            ('Среднее зелье здоровья', 'Восстанавливает 25% HP', '❤️', 'hp', 25, 250),
            ('Сильное зелье здоровья', 'Восстанавливает 40% HP', '❤️', 'hp', 40, 1000),
            ('Слабое зелье маны', 'Восстанавливает 10% MP', '💧', 'mana', 10, 20),
            ('Среднее зелье маны', 'Восстанавливает 25% MP', '💧', 'mana', 25, 250),
            ('Сильное зелье маны', 'Восстанавливает 40% MP', '💧', 'mana', 40, 1000),
            ('Слабое зелье выносливости', 'Восстанавливает 10% выносливости', '⚡', 'stamina', 10, 20),
            ('Среднее зелье выносливости', 'Восстанавливает 25% выносливости', '⚡', 'stamina', 25, 250),
            ('Сильное зелье выносливости', 'Восстанавливает 40% выносливости', '⚡', 'stamina', 40, 1000),
            ('Голубой кристалл', 'Для заточки оружия и брони. Увеличивает шанс заточки на 15%', '🔵', 'crystal', 15, 200),
            ('Фиолетовый кристалл', 'Для заточки оружия и брони. Увеличивает шанс заточки на 35%', '🟣', 'crystal', 35, 500),
            ('Красный кристалл', 'Для заточки оружия и брони. Увеличивает шанс заточки на 55%', '🔴', 'crystal', 55, 1200),
            ('Свиток снятия проклятия', 'Снимает любое проклятие или печать башни', '📜', 'curse_remove', 0, 0),
        ]
        cur.executemany('''
            INSERT INTO consumable_templates (name, description, icon, restore_type, restore_percent, price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', consumables)
        conn.commit()
    conn.close()


def seed_herbs():
    """Заполнение трав"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM herbs')
    if cur.fetchone()[0] == 0:
        herbs = [
            ('Зверобой', '🌿', 5, 'Целебная трава, растущая на лугах'),
            ('Мелисса', '🌱', 5, 'Ароматная трава, успокаивает нервы'),
            ('Полынь', '🌿', 5, 'Горькая трава, используется в зельях'),
            ('Крапива', '🌿', 5, 'Жгучая трава, полезна для здоровья'),
            ('Лаванда', '🌸', 5, 'Душистая трава, помогает от бессонницы'),
            ('Тысячелистник', '🌿', 5, 'Кровоостанавливающая трава'),
            ('Ромашка', '🌼', 5, 'Успокаивающая трава'),
            ('Чабрец', '🌿', 5, 'Пряная трава, укрепляет иммунитет')
        ]
        cur.executemany('INSERT INTO herbs (name, icon, price, description) VALUES (?, ?, ?, ?)', herbs)
        conn.commit()
    conn.close()


def seed_guild_quests():
    """Заполнение гильдейских квестов"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM guild_quests')
    if cur.fetchone()[0] == 0:
        quests = [
            ('Сопровождение каравана', 'Сопроводите торговый караван до соседнего города.', 60, 450, 800, None, None, None, None),
            ('Разведка местности', 'Исследуйте окрестности и доложите обстановку.', 30, 350, 300, 'consumable', 1, 1, None),
            ('Сбор редких трав', 'Соберите редкие травы для лекаря.', 60, 150, 700, 'herb', None, 10, None),
            ('Уничтожение гнезда монстров', 'Очистите гнездо монстров в лесу.', 240, 1500, 0, 'equipment', None, 1, 2),
            ('Доставка оружия в крепость', 'Перевезите оружие в крепость.', 30, 100, 200, 'item', None, 1, 2),
            ('Эскорт посла', 'Сопроводите посла в столицу.', 90, 250, 1000, 'consumable', 2, 1, None),
            ('Сбор информации в городе', 'Соберите информацию о врагах.', 15, 60, 100, None, None, None, None),
            ('Спасение пленников', 'Освободите пленников из лагеря бандитов.', 90, 600, 500, None, None, None, None),
            ('Охота на нежить', 'Очистите кладбище от нежити.', 120, 800, 300, 'consumable', 7, 1, None),
            ('Помощь кузнецу', 'Помогите кузнецу с заказом.', 60, 300, 500, 'crystal', None, 1, None),
        ]
        cur.executemany('''
            INSERT INTO guild_quests (name, description, duration_minutes, exp_reward, silver_reward,
                                      extra_reward_type, extra_reward_id, extra_reward_quantity, extra_reward_rarity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', quests)
        conn.commit()
    conn.close()


def seed_premium_shop():
    """Заполнение премиум-магазина"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM premium_shop')
    if cur.fetchone()[0] == 0:
        items = [
            ('Набор слабых кристаллов (10 шт)', '10 слабых кристаллов заточки (+15% каждый)', '💎', 20, 'crystal_pack', '{"crystal_type": "weak", "count": 10}'),
            ('Набор средних кристаллов (5 шт)', '5 средних кристаллов заточки (+35% каждый)', '💎', 30, 'crystal_pack', '{"crystal_type": "medium", "count": 5}'),
            ('Набор сильных кристаллов (3 шт)', '3 сильных кристалла заточки (+55% каждый)', '💎', 60, 'crystal_pack', '{"crystal_type": "strong", "count": 3}'),
            ('Свиток снятия проклятия', 'Снимает любое проклятие (Проклятие или Печать башни)', '📜', 10, 'scroll', '{"effect": "remove_curse"}'),
            ('VIP Серебряный (25%)', '+25% к опыту и серебру на 30 дней', '⬜', 300, 'vip', '{"vip_level": 2, "bonus": 25}'),
            ('VIP Золотой (50%)', '+50% к опыту и серебру на 30 дней', '🌟', 600, 'vip', '{"vip_level": 3, "bonus": 50}'),
            ('VIP Алмазный (100%)', '+100% к опыту и серебру на 30 дней', '👑', 1200, 'vip', '{"vip_level": 5, "bonus": 100}'),
        ]
        cur.executemany('''
            INSERT INTO premium_shop (name, description, icon, price, item_type, item_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', items)
        conn.commit()
    conn.close()


def add_vip_columns():
    """Добавляет колонки VIP в таблицу characters если их нет"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute("PRAGMA table_info(characters)")
    columns = [col[1] for col in cur.fetchall()]
    
    if 'vip' not in columns:
        cur.execute('ALTER TABLE characters ADD COLUMN vip INTEGER DEFAULT 0')
        print("✅ Добавлена колонка vip")
    
    if 'vip_expires_at' not in columns:
        cur.execute('ALTER TABLE characters ADD COLUMN vip_expires_at TIMESTAMP DEFAULT NULL')
        print("✅ Добавлена колонка vip_expires_at")
    
    conn.commit()
    conn.close()