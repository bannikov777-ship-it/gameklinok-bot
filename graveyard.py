# graveyard.py
import random

GRAVEYARD_IMAGES = {
    'Скелет-воин': 'photo-240828623_456239301',
    'Зомби-могильщик': 'photo-240828623_456239303',
    'Призрак-странник': 'photo-240828623_456239302',
    'Гнилой пёс': 'photo-240828623_456239306',
    'Гуль': 'photo-240828623_456239310',
    'Рыцарь-мертвец': 'photo-240828623_456239305',
    'Вампир-недоучка': 'photo-240828623_456239307',
    'Некромант-ученик': 'photo-240828623_456239308',
    'Баньши': 'photo-240828623_456239309',
    'Костяной голем': 'photo-240828623_456239310',
    'Лич-повелитель': 'photo-240828623_456239311',
    'Костяной дракон': 'photo-240828623_456239313',
}

GRAVEYARD_MONSTERS = {
    'weak': [
        {'name': 'Скелет-воин', 'base_hp': 60, 'base_attack': 7, 'base_defense': 5, 'exp': 30, 'silver': 35, 'description': 'Кости, оживлённые тёмной магией.'},
        {'name': 'Зомби-могильщик', 'base_hp': 65, 'base_attack': 8, 'base_defense': 4, 'exp': 35, 'silver': 40, 'description': 'Разлагающийся труп с лопатой.'},
        {'name': 'Призрак-странник', 'base_hp': 55, 'base_attack': 8, 'base_defense': 8, 'exp': 25, 'silver': 35, 'description': 'Бестелесный дух, шепчет проклятия.'},
        {'name': 'Гнилой пёс', 'base_hp': 45, 'base_attack': 5, 'base_defense': 1, 'exp': 20, 'silver': 25, 'description': 'Бывший сторожевой пёс, теперь ищет живую плоть.'},
        {'name': 'Гуль', 'base_hp': 55, 'base_attack': 7, 'base_defense': 3, 'exp': 30, 'silver': 40, 'description': 'Пожиратель плоти. Его когти отравлены.'}
    ],
    'medium': [
        {'name': 'Рыцарь-мертвец', 'base_hp': 105, 'base_attack': 18, 'base_defense': 16, 'exp': 90, 'silver': 65, 'description': 'Бывший паладин, павший в бою.'},
        {'name': 'Вампир-недоучка', 'base_hp': 80, 'base_attack': 20, 'base_defense': 10, 'exp': 85, 'silver': 60, 'description': 'Молодой вампир, ещё не набравший силы.'},
        {'name': 'Некромант-ученик', 'base_hp': 75, 'base_attack': 35, 'base_defense': 0, 'exp': 80, 'silver': 50, 'description': 'Тёмный маг, поднимающий мертвецов.'},
        {'name': 'Баньши', 'base_hp': 50, 'base_attack': 32, 'base_defense': 15, 'exp': 75, 'silver': 55, 'description': 'Женщина-призрак, её крик пронзает душу.'},
        {'name': 'Костяной голем', 'base_hp': 110, 'base_attack': 38, 'base_defense': 10, 'exp': 85, 'silver': 60, 'description': 'Голем из костей. Почти не чувствует боли.'}
    ],
    'boss': [
        {'name': 'Лич-повелитель', 'base_hp': 180, 'base_attack': 45, 'base_defense': 20, 'exp': 250, 'silver': 180, 'description': 'Могущественный лич, воскресший из праха.'},
        {'name': 'Костяной дракон', 'base_hp': 250, 'base_attack': 65, 'base_defense': 25, 'exp': 300, 'silver': 250, 'description': 'Скелет дракона, оживлённый древней магией.'}
    ]
}

def get_graveyard_monster_by_depth(depth):
    if depth <= 3:
        pool = GRAVEYARD_MONSTERS['weak']
        tier = 1
        is_boss = False
    elif depth <= 6:
        if random.random() < 0.5:
            pool = GRAVEYARD_MONSTERS['weak']
            tier = 1
        else:
            pool = GRAVEYARD_MONSTERS['medium']
            tier = 2
        is_boss = False
    elif depth <= 9:
        if random.random() < 0.3:
            pool = GRAVEYARD_MONSTERS['weak']
            tier = 1
        else:
            pool = GRAVEYARD_MONSTERS['medium']
            tier = 2
        is_boss = False
    else:
        boss_chance = 10 + (depth - 10) * 2
        boss_chance = min(boss_chance, 50)
        if random.random() < boss_chance / 100:
            pool = GRAVEYARD_MONSTERS['boss']
            tier = 3
            is_boss = True
        else:
            if random.random() < 0.3:
                pool = GRAVEYARD_MONSTERS['weak']
                tier = 1
            else:
                pool = GRAVEYARD_MONSTERS['medium']
                tier = 2
            is_boss = False
    
    base = random.choice(pool)
    monster_level = max(1, depth // 2 + 1)
    hp = base['base_hp'] * (1 + (monster_level - 1) * 0.2)
    attack = base['base_attack'] * (1 + (monster_level - 1) * 0.15)
    defense = base['base_defense'] * (1 + (monster_level - 1) * 0.1)
    exp = base['exp'] * (1 + (monster_level - 1) * 0.2)
    silver = base['silver'] * (1 + (monster_level - 1) * 0.2)
    return {
        'name': base['name'],
        'hp': round(hp),
        'max_hp': round(hp),
        'attack': round(attack),
        'defense': round(defense),
        'exp': round(exp),
        'silver': round(silver),
        'description': base.get('description', ''),
        'drop_chance': 0.25,
        'level': monster_level,
        'tier': tier,
        'is_boss': is_boss,
        'zone': 'graveyard',
        'image': GRAVEYARD_IMAGES.get(base['name'])
    }

def generate_graveyard_monster(depth):
    return get_graveyard_monster_by_depth(depth)

def check_graveyard_chest():
    if random.random() < 0.005:
        chest_type = random.random()
        if chest_type < 0.8:
            silver = random.randint(100, 1000)
            return {
                'type': 'silver',
                'amount': silver,
                'text': f'💰 Вы нашли сундук с {silver} серебра!'
            }
        elif chest_type < 0.95:
            return {
                'type': 'item',
                'rarity': 1,
                'text': '🗡️ Вы нашли сундук с зелёным предметом (1⭐)!'
            }
        else:
            rarity = 2 if random.random() < 0.75 else 3
            rarity_name = 'синим' if rarity == 2 else 'фиолетовым'
            return {
                'type': 'item',
                'rarity': rarity,
                'text': f'🗡️ Вы нашли сундук с {rarity_name} предметом ({rarity}⭐)!'
            }
    return None