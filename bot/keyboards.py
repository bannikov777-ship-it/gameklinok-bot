# keyboards.py (исправленный с go_* навигацией)
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

# ---- БАЗОВЫЕ КЛАВИАТУРЫ ----
def get_back_keyboard(parent_name='город'):
    keyboard = VkKeyboard()
    keyboard.add_button('👤 Профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'profile'})
    keyboard.add_button(f'🏙️ В {parent_name}', color=VkKeyboardColor.SECONDARY, payload={'cmd': f'go_{parent_name}'})
    return keyboard

def get_lore_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('⚔ Создать персонажа', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'create_character'})
    return keyboard

def get_gender_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('♂ Мужской', color=VkKeyboardColor.PRIMARY, payload={'gender': 'male'})
    keyboard.add_button('♀ Женский', color=VkKeyboardColor.PRIMARY, payload={'gender': 'female'})
    return keyboard

def get_class_choice_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('🛡 Оруженосец', color=VkKeyboardColor.PRIMARY, payload={'class': 'Оруженосец'})
    keyboard.add_button('🏹 Охотник', color=VkKeyboardColor.PRIMARY, payload={'class': 'Охотник'})
    keyboard.add_line()
    keyboard.add_button('✨ Послушник', color=VkKeyboardColor.PRIMARY, payload={'class': 'Послушник'})
    return keyboard

# ---- ПРОФИЛЬ И ИНВЕНТАРЬ ----
def get_profile_keyboard():
    """Клавиатура для профиля"""
    keyboard = VkKeyboard()
    keyboard.add_button('📬 Почта', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'mail'})
    keyboard.add_button('🎁 Промокод', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'code_menu'})
    keyboard.add_line()
    keyboard.add_button('🎒 Инвентарь', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'inventory'})
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    return keyboard

def get_inventory_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('👤 В профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_profile'})
    return keyboard

def get_inventory_actions_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('🎒 Экипировать', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'inventory_equip'})
    keyboard.add_button('❌ Снять', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'inventory_unequip'})
    keyboard.add_line()
    keyboard.add_button('👤 В профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_profile'})
    return keyboard

def get_inventory_equip_slot_keyboard(char=None):
    """Клавиатура выбора слота для экипировки (с учетом класса)"""
    keyboard = VkKeyboard()
    keyboard.add_button('🎩 Голова', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'inv_equip_slot', 'slot': 'head'})
    
    # Левая рука ТОЛЬКО если есть класс (уровень 20+)
    if char and char.get('class') and char.get('level', 0) >= 20:
        keyboard.add_button('⚔️ Лев. рука', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'inv_equip_slot', 'slot': 'weapon_left'})
    
    keyboard.add_line()
    keyboard.add_button('🗡️ Прав. рука', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'inv_equip_slot', 'slot': 'weapon_right'})
    keyboard.add_button('🛡️ Броня', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'inv_equip_slot', 'slot': 'armor'})
    keyboard.add_line()
    keyboard.add_button('👢 Сапоги', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'inv_equip_slot', 'slot': 'boots'})
    keyboard.add_line()
    keyboard.add_button('🎒 В инвентарь', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_inventory'})
    return keyboard

def get_inventory_unequip_slot_keyboard(equipment):
    keyboard = VkKeyboard()
    slots = {
        'head': '🎩 Голова',
        'weapon_left': '⚔️ Левая рука',
        'weapon_right': '🗡️ Правая рука',
        'armor': '🛡️ Броня',
        'boots': '👢 Сапоги'
    }
    for slot_key, slot_name in slots.items():
        if slot_key in equipment and equipment[slot_key]:
            keyboard.add_button(slot_name, color=VkKeyboardColor.PRIMARY, 
                               payload={'cmd': 'inv_unequip_slot', 'slot': slot_key})
    keyboard.add_line()
    keyboard.add_button('🎒 В инвентарь', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_inventory'})
    return keyboard

# ---- ГОРОД ----
def get_city_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('🍺 Таверна', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'tavern'})
    keyboard.add_button('🏛 Ратуша', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'town_hall'})
    keyboard.add_line()
    keyboard.add_button('🏰 Гильдия', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild'})
    keyboard.add_button('🏪 Рынок', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market'})
    keyboard.add_line()
    keyboard.add_button('🏹 Гильдия охотников', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'hunters'})
    keyboard.add_button('⛪ Собор', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'church'})
    keyboard.add_line()
    keyboard.add_button('💎 Премиум магазин', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'premium_shop'})
    keyboard.add_line()
    keyboard.add_button('🚪 Выход из города', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'exit_city'})
    return keyboard

def get_city2_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('🚪 Выйти из города', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'exit_city2'})
    return keyboard

# ---- ВЫХОД ИЗ ГОРОДА ----
def get_exit_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('🌲 Лес (1 ур.)', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'forest'})
    keyboard.add_button('🪦 Кладбище (10 ур.)', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'graveyard'})
    keyboard.add_line()
    keyboard.add_button('🌿 Луг', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'go_meadow'})
    keyboard.add_line()
    keyboard.add_button('👤 Профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'profile'})
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    return keyboard

# ---- ЛУГ ----
def get_meadow_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('🌿 Собрать травы', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'meadow_herbs'})
    keyboard.add_button('🗼 Путь к башне', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'meadow_tower'})
    keyboard.add_line()
    keyboard.add_button('🚪 К воротам', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_exit'})  # ✅ исправлено
    keyboard.add_button('🏙️ Озерный край', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'meadow_city'})
    return keyboard

# ---- ТАВЕРНА ----
def get_tavern_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('📜 Квесты', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'tavern_quests'})
    keyboard.add_button('🛏 Комната', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'tavern_room'})
    keyboard.add_line()
    keyboard.add_button('🗣 Слухи', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'tavern_rumors'})
    keyboard.add_button('🍖 Еда', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'tavern_food'})
    keyboard.add_line()
    keyboard.add_button('👤 Профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'profile'})
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    return keyboard

def get_food_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('🍞 Хлеб (20% HP) - 60💰', color=VkKeyboardColor.PRIMARY,
                        payload={'cmd': 'buy_food', 'percent': 20, 'price': 60})
    keyboard.add_button('🍗 Мясо (50% HP) - 120💰', color=VkKeyboardColor.PRIMARY,
                        payload={'cmd': 'buy_food', 'percent': 50, 'price': 120})
    keyboard.add_button('🍲 Ужин (100% HP) - 220💰', color=VkKeyboardColor.PRIMARY,
                        payload={'cmd': 'buy_food', 'percent': 100, 'price': 220})
    keyboard.add_line()
    keyboard.add_button('🍺 В таверну', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_tavern'})
    return keyboard

def get_sleep_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('🛏 1 час (20% HP)', color=VkKeyboardColor.PRIMARY,
                        payload={'cmd': 'sleep', 'hours': 1, 'percent': 20})
    keyboard.add_button('🛏 2 часа (50% HP)', color=VkKeyboardColor.PRIMARY,
                        payload={'cmd': 'sleep', 'hours': 2, 'percent': 50})
    keyboard.add_button('🛏 3 часа (100% HP)', color=VkKeyboardColor.PRIMARY,
                        payload={'cmd': 'sleep', 'hours': 3, 'percent': 100})
    keyboard.add_line()
    keyboard.add_button('🍺 В таверну', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_tavern'})
    return keyboard

def get_sleep_status_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('⏳ Проверить время', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'sleep_check'})
    keyboard.add_button('🚪 Выйти (отменить сон)', color=VkKeyboardColor.NEGATIVE, payload={'cmd': 'sleep_cancel'})
    return keyboard

# ---- РАТУША ----
def get_town_hall_keyboard(char):
    keyboard = VkKeyboard()
    keyboard.add_button('🎯 Выбор класса', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'town_hall_class'})
    keyboard.add_button('🛠 Создать гильдию', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_create'})
    keyboard.add_line()
    keyboard.add_button('📊 Рейтинг', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'rating'})
    keyboard.add_line()
    keyboard.add_button('👤 Профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'profile'})
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    return keyboard

# ---- РЫНОК ----
def get_market_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('🏪 Магазин', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market_shop'})
    keyboard.add_button('🏛 Аукцион', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market_auction'})
    keyboard.add_line()
    keyboard.add_button('⚒ Кузница', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'smithy'})
    keyboard.add_button('💊 Лекарь', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'market_healer'})
    keyboard.add_line()
    keyboard.add_button('👤 Профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'profile'})
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    return keyboard

# ---- АУКЦИОН ----
def get_auction_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('🔄 Обновить', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'auction_refresh'})
    keyboard.add_button('📤 Выставить', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'auction_sell'})
    keyboard.add_line()
    keyboard.add_button('🏪 На рынок', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_market'})
    return keyboard

# ---- ГИЛЬДИЯ ОХОТНИКОВ ----
def get_hunters_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('💰 Сдать трофеи', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'hunters_sell'})
    keyboard.add_button('📜 Взять задание', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'hunters_quests'})
    keyboard.add_line()
    keyboard.add_button('📋 Мои задания', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'hunters_my_quests'})
    keyboard.add_line()
    keyboard.add_button('👤 Профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'profile'})
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    return keyboard

# ---- СОБОР ----
def get_church_keyboard(char):
    keyboard = VkKeyboard()
    if char.get('debuff') == 1:
        keyboard.add_button('💰 Снять проклятие (1000💰)', color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'church_remove_debuff'})
        keyboard.add_line()
    elif char.get('debuff') == 2:
        keyboard.add_button('💰 Снять печать башни (3000💰)', color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'church_remove_tower_debuff'})
        keyboard.add_line()
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    return keyboard

# ---- ЛЕКАРЬ ----
def get_healer_keyboard(templates):
    keyboard = VkKeyboard()
    hp_pots = [t for t in templates if t['restore_type'] == 'hp']
    mana_pots = [t for t in templates if t['restore_type'] == 'mana']
    stamina_pots = [t for t in templates if t['restore_type'] == 'stamina']

    for t in hp_pots:
        label = f"{t['icon']} {t['restore_percent']}% HP - {t['price']}💰"
        keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'buy_consumable', 'template_id': t['id'], 'price': t['price']})
    keyboard.add_line()

    for t in mana_pots:
        label = f"{t['icon']} {t['restore_percent']}% MP - {t['price']}💰"
        keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'buy_consumable', 'template_id': t['id'], 'price': t['price']})
    keyboard.add_line()

    for t in stamina_pots:
        label = f"{t['icon']} {t['restore_percent']}% ST - {t['price']}💰"
        keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'buy_consumable', 'template_id': t['id'], 'price': t['price']})
    keyboard.add_line()

    keyboard.add_button('🏪 На рынок', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_market'})
    return keyboard

# ---- БОЙ ----
def get_battle_keyboard(player_class):
    keyboard = VkKeyboard()
    keyboard.add_button('⚔ Атака', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'battle_attack'})
    keyboard.add_button('🛡 Защита (10% STA)', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'battle_defend'})
    keyboard.add_line()
    keyboard.add_button('🌀 Парирование', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'battle_parry'})
    if player_class == 'Оруженосец':
        keyboard.add_button('🛡 Стойка', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'battle_super'})
    elif player_class == 'Охотник':
        keyboard.add_button('🏹 Меткий выстрел', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'battle_super'})
    elif player_class == 'Послушник':
        keyboard.add_button('✨ Исцеление', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'battle_magic'})
    keyboard.add_line()
    keyboard.add_button('💊 Зелье', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'battle_potion'})
    keyboard.add_button('🏃 Сбежать', color=VkKeyboardColor.NEGATIVE, payload={'cmd': 'battle_flee'})
    return keyboard

def get_after_battle_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('🌲 В глубь леса', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'forest_deep'})
    keyboard.add_button('🚶 Побродить', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'forest_wander'})
    keyboard.add_line()
    keyboard.add_button('🚪 К выходу', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'back_to_exit'})
    return keyboard

def get_graveyard_after_battle_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('🪦 В глубь кладбища', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'graveyard_deep'})
    keyboard.add_button('🚶 Побродить', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'graveyard_wander'})
    keyboard.add_line()
    keyboard.add_button('🚪 К выходу', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'back_to_exit'})
    return keyboard

# ---- ГИЛЬДИЯ ----
def get_guild_keyboard(guild, my_rank):
    keyboard = VkKeyboard()
    keyboard.add_button('👥 Список участников', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_members'})
    keyboard.add_button('📦 Склад', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_storage'})
    keyboard.add_line()
    keyboard.add_button('📊 Статистика', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_stats'})
    
    # Заявки (только для руководства)
    if my_rank in ('Лидер', 'Заместитель', 'Офицер'):
        keyboard.add_button('📋 Заявки', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_applications'})
    
    keyboard.add_line()
    if my_rank in ('Лидер', 'Заместитель'):
        keyboard.add_button('⚙️ Управление', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_manage'})
    keyboard.add_button('💬 Чат', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_chat'})
    keyboard.add_line()
    keyboard.add_button('📜 Квесты гильдии', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_quests'})
    keyboard.add_button('📌 Мой квест', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_quest_status'})
    keyboard.add_line()
    keyboard.add_button('👤 Профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'profile'})
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    return keyboard

def get_guild_menu_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('📋 Список гильдий', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_list'})
    keyboard.add_line()
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    return keyboard

def get_guild_manage_keyboard(members, my_rank):
    keyboard = VkKeyboard()
    for m in members:
        if m['rank'] == 'Лидер':
            continue
        if my_rank == 'Лидер' or (my_rank == 'Заместитель' and m['rank'] != 'Заместитель'):
            keyboard.add_button(f"📌 {m['name']}", color=VkKeyboardColor.PRIMARY, 
                               payload={'cmd': 'guild_manage_member', 'member_id': m['id']})
            keyboard.add_line()
    keyboard.add_button('🏰 В гильдию', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_guild'})
    return keyboard

def get_member_action_keyboard(member_id, current_rank):
    keyboard = VkKeyboard()
    keyboard.add_button('🟢 Назначить офицером', color=VkKeyboardColor.PRIMARY, 
                       payload={'cmd': 'guild_set_rank', 'member_id': member_id, 'rank': 'Офицер'})
    keyboard.add_button('🔵 Назначить заместителем', color=VkKeyboardColor.PRIMARY, 
                       payload={'cmd': 'guild_set_rank', 'member_id': member_id, 'rank': 'Заместитель'})
    keyboard.add_line()
    keyboard.add_button('❌ Исключить', color=VkKeyboardColor.NEGATIVE, 
                       payload={'cmd': 'guild_kick', 'member_id': member_id})
    keyboard.add_line()
    keyboard.add_button('⚙️ В управление', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'guild_manage'})
    return keyboard

def get_guild_chat_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('📝 Написать в чат', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_chat_send'})
    keyboard.add_line()
    keyboard.add_button('🏰 В гильдию', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_guild'})
    return keyboard

def get_guild_storage_keyboard(items):
    keyboard = VkKeyboard()
    
    if items:
        for item in items:
            label = f"{item['icon']} {item['name']} x{item['quantity']}"
            keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                               payload={'cmd': 'guild_storage_item', 'storage_id': item['id']})
            keyboard.add_line()
    else:
        keyboard.add_button('📭 Склад пуст', color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
    
    keyboard.add_button('➕ Добавить предмет', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_storage_add'})
    keyboard.add_button('➖ Изъять предмет', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'guild_storage_remove_prompt'})
    keyboard.add_line()
    keyboard.add_button('🏰 В гильдию', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_guild'})
    return keyboard

# ---- БАШНЯ ----
def get_tower_chat_keyboard():
    """Клавиатура для чата башни"""
    keyboard = VkKeyboard()
    keyboard.add_button('📝 Написать в чат', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'tower_chat_send'})
    keyboard.add_line()
    keyboard.add_button('🏰 В башню', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_tower'})
    return keyboard

# ---- ПОЧТА ----
def get_mail_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('📝 Написать письмо', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'mail_write'})
    keyboard.add_line()
    keyboard.add_button('👤 В профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_profile'})
    return keyboard


def get_mail_read_keyboard(has_attachment=False):
    keyboard = VkKeyboard()
    if has_attachment:
        keyboard.add_button('📥 Забрать вложение', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'mail_claim_attachment'})
        keyboard.add_line()
    keyboard.add_button('🗑 Удалить', color=VkKeyboardColor.NEGATIVE, payload={'cmd': 'mail_delete'})
    keyboard.add_button('📬 На почту', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_profile'})
    return keyboard


def get_mail_attachment_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('💰 Деньги', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'mail_attach_money'})
    keyboard.add_button('🗡️ Предметы', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'mail_attach_item'})
    keyboard.add_line()
    keyboard.add_button('📝 Без вложения', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'mail_attach_none'})
    keyboard.add_button('📬 На почту', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_profile'})
    return keyboard