# monsters.py
import random
from utils import exp_to_next_level

FOREST_IMAGES = {
    'Гоблин-разведчик': 'photo-240828623_456239290',
    'Лесной крыс': 'photo-240828623_456239289',
    'Волк-одиночка': 'photo-240828623_456239288',
    'Зомби-лесник': 'photo-240828623_456239287',
    'Енот-переросток': 'photo-240828623_456239286',
    'Лесной тролль': 'photo-240828623_456239285',
    'Ядовитый паук': 'photo-240828623_456239284',
    'Оборотень-неудачник': 'photo-240828623_456239283',
    'Лесная гарпия': 'photo-240828623_456239282',
    'Древень': 'photo-240828623_456239281',
    'Лесной великан': 'photo-240828623_456239275',
    'Ведьма-лесовичка': 'photo-240828623_456239280',
}

FOREST_MONSTERS = {
    'weak': [
        {'name': 'Гоблин-разведчик', 'base_hp': 25, 'base_attack': 5, 'base_defense': 2, 'exp': 15, 'silver': 10, 'description': 'Маленький, но юркий. Опасен в стае.'},
        {'name': 'Лесной крыс', 'base_hp': 15, 'base_attack': 3, 'base_defense': 0, 'exp': 5, 'silver': 5, 'description': 'Грызун размером с собаку. Зубы острые.'},
        {'name': 'Волк-одиночка', 'base_hp': 25, 'base_attack': 6, 'base_defense': 2, 'exp': 20, 'silver': 10, 'description': 'Худой, но злой. Лучше не встречаться с ним в темноте.'},
        {'name': 'Зомби-лесник', 'base_hp': 30, 'base_attack': 6, 'base_defense': 3, 'exp': 20, 'silver': 10, 'description': 'Бывший охотник. Теперь ищет живую плоть.'},
        {'name': 'Енот-переросток', 'base_hp': 20, 'base_attack': 3, 'base_defense': 1, 'exp': 10, 'silver': 5, 'description': 'Злой и пушистый. Ворует еду у путников.'}
    ],
    'medium': [
        {'name': 'Лесной тролль', 'base_hp': 55, 'base_attack': 10, 'base_defense': 4, 'exp': 40, 'silver': 20, 'description': 'Огромный, неуклюжий, но очень сильный.'},
        {'name': 'Ядовитый паук', 'base_hp': 45, 'base_attack': 12, 'base_defense': 2, 'exp': 30, 'silver': 15, 'description': 'Плетёт сети и ждёт жертв. Его укус смертелен для слабых.'},
        {'name': 'Оборотень-неудачник', 'base_hp': 50, 'base_attack': 12, 'base_defense': 5, 'exp': 35, 'silver': 20, 'description': 'Получеловек-полуволк. Вечно на кого-то злится.'},
        {'name': 'Лесная гарпия', 'base_hp': 45, 'base_attack': 13, 'base_defense': 2, 'exp': 35, 'silver': 25, 'description': 'Птица с лицом женщины. Её крик оглушает.'},
        {'name': 'Древень', 'base_hp': 70, 'base_attack': 12, 'base_defense': 7, 'exp': 45, 'silver': 40, 'description': 'Ожившее дерево. Медленное, но очень прочное.'}
    ],
    'boss': [
        {'name': 'Лесной великан', 'base_hp': 125, 'base_attack': 20, 'base_defense': 15, 'exp': 120, 'silver': 150, 'description': 'Древний хранитель леса. Сокрушит любого.'},
        {'name': 'Ведьма-лесовичка', 'base_hp': 80, 'base_attack': 30, 'base_defense': 0, 'exp': 100, 'silver': 90, 'description': 'Злая колдунья из чащи. Знает тёмные заклинания.'}
    ]
}

def get_forest_monster_by_depth(depth):
    if depth <= 3:
        pool = FOREST_MONSTERS['weak']
        tier = 1
        is_boss = False
    elif depth <= 6:
        if random.random() < 0.5:
            pool = FOREST_MONSTERS['weak']
            tier = 1
        else:
            pool = FOREST_MONSTERS['medium']
            tier = 2
        is_boss = False
    elif depth <= 9:
        if random.random() < 0.3:
            pool = FOREST_MONSTERS['weak']
            tier = 1
        else:
            pool = FOREST_MONSTERS['medium']
            tier = 2
        is_boss = False
    else:
        boss_chance = 10 + (depth - 10) * 2
        boss_chance = min(boss_chance, 50)
        if random.random() < boss_chance / 100:
            pool = FOREST_MONSTERS['boss']
            tier = 3
            is_boss = True
        else:
            if random.random() < 0.3:
                pool = FOREST_MONSTERS['weak']
                tier = 1
            else:
                pool = FOREST_MONSTERS['medium']
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
        'image': FOREST_IMAGES.get(base['name'])
    }

def generate_monster(zone, depth=0):
    if zone == 'forest':
        return get_forest_monster_by_depth(depth)
    elif zone == 'graveyard':
        from graveyard import generate_graveyard_monster
        return generate_graveyard_monster(depth)
    return None