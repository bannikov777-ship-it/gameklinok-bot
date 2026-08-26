# crafting.py
import sqlite3
from config import DB_NAME
from resources import get_resource_id_by_name

def get_herb_id_by_name(name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM herbs WHERE name = ?', (name,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def seed_craft_recipes():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM craft_recipes')
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    herb_ids = {}
    for name in ['Зверобой', 'Мелисса', 'Ромашка', 'Полынь', 'Крапива', 'Лаванда']:
        herb_ids[name] = get_herb_id_by_name(name)

    res_ids = {}
    for name in ['Шкура', 'Коготь', 'Зуб', 'Магическая эссенция', 'Кости', 'Прах', 'Тёмная эссенция', 'Череп', 'Кровавый камень']:
        res_ids[name] = get_resource_id_by_name(name)

    potion_ids = {}
    conn2 = sqlite3.connect(DB_NAME)
    cur2 = conn2.cursor()
    for name in ['Слабое зелье здоровья', 'Среднее зелье здоровья', 'Сильное зелье здоровья',
                 'Слабое зелье маны', 'Среднее зелье маны', 'Слабое зелье выносливости']:
        cur2.execute('SELECT id FROM consumable_templates WHERE name = ?', (name,))
        row = cur2.fetchone()
        if row:
            potion_ids[name] = row[0]
    conn2.close()

    recipes_data = [
        ('potion', potion_ids.get('Слабое зелье здоровья'), 1,
         'herb', herb_ids.get('Зверобой'), 3, 'herb', herb_ids.get('Мелисса'), 3, 'herb', herb_ids.get('Ромашка'), 2),
        ('potion', potion_ids.get('Слабое зелье маны'), 1,
         'herb', herb_ids.get('Мелисса'), 3, 'herb', herb_ids.get('Полынь'), 3, 'herb', herb_ids.get('Крапива'), 2),
        ('potion', potion_ids.get('Слабое зелье выносливости'), 1,
         'herb', herb_ids.get('Зверобой'), 3, 'herb', herb_ids.get('Крапива'), 3, 'herb', herb_ids.get('Лаванда'), 2),
        ('potion', potion_ids.get('Среднее зелье здоровья'), 1,
         'herb', herb_ids.get('Зверобой'), 5, 'resource', res_ids.get('Шкура'), 3, 'resource', res_ids.get('Зуб'), 3),
        ('potion', potion_ids.get('Среднее зелье маны'), 1,
         'herb', herb_ids.get('Мелисса'), 5, 'resource', res_ids.get('Коготь'), 3, 'resource', res_ids.get('Магическая эссенция'), 2),
        ('potion', potion_ids.get('Сильное зелье здоровья'), 1,
         'resource', res_ids.get('Кости'), 5, 'resource', res_ids.get('Прах'), 3, 'resource', res_ids.get('Кровавый камень'), 1),
        ('potion', potion_ids.get('Сильное зелье маны'), 1,
         'resource', res_ids.get('Кости'), 5, 'resource', res_ids.get('Тёмная эссенция'), 3, 'resource', res_ids.get('Череп'), 1),
    ]

    recipes = []
    for r in recipes_data:
        valid = True
        if r[1] is None:
            print(f"⚠️ Пропускаем рецепт: результат не найден")
            continue
        for i in range(4, len(r), 3):
            if r[i] is None or r[i+1] is None:
                valid = False
                print(f"⚠️ Пропускаем рецепт: ингредиент не найден")
                break
        if valid:
            recipes.append(r)

    if recipes:
        cur.executemany('''
            INSERT INTO craft_recipes 
            (result_type, result_id, result_quantity, 
             ingredient1_type, ingredient1_id, ingredient1_quantity,
             ingredient2_type, ingredient2_id, ingredient2_quantity,
             ingredient3_type, ingredient3_id, ingredient3_quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', recipes)
        conn.commit()
        print(f"✅ Добавлено {len(recipes)} рецептов")
    else:
        print("⚠️ Нет валидных рецептов для добавления")
    conn.close()

def get_craft_recipes():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute('''
            SELECT id, result_type, result_id, result_quantity,
                   ingredient1_type, ingredient1_id, ingredient1_quantity,
                   ingredient2_type, ingredient2_id, ingredient2_quantity,
                   ingredient3_type, ingredient3_id, ingredient3_quantity
            FROM craft_recipes
        ''')
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        conn.close()
        print("⚠️ Ошибка структуры craft_recipes. Удалите game.db и перезапустите бота.")
        return []
    conn.close()

    recipes = []
    for row in rows:
        recipe = {
            'id': row[0],
            'result_type': row[1],
            'result_id': row[2],
            'result_quantity': row[3],
            'ingredients': []
        }
        for i in range(1, 4):
            base = 3 + (i-1)*3
            ing_type = row[base]
            ing_id = row[base + 1]
            ing_qty = row[base + 2]
            if ing_type and ing_id:
                recipe['ingredients'].append({
                    'type': ing_type,
                    'id': ing_id,
                    'quantity': ing_qty
                })

        if recipe['result_type'] == 'potion':
            conn2 = sqlite3.connect(DB_NAME)
            cur2 = conn2.cursor()
            cur2.execute('SELECT name, icon, restore_percent, restore_type FROM consumable_templates WHERE id = ?', (recipe['result_id'],))
            res = cur2.fetchone()
            conn2.close()
            if res:
                recipe['result_name'] = res[0]
                recipe['result_icon'] = res[1]
                recipe['restore_percent'] = res[2]
                recipe['restore_type'] = res[3]
            else:
                recipe['result_name'] = 'Неизвестное зелье'
                recipe['result_icon'] = '❓'
                recipe['restore_percent'] = 0
                recipe['restore_type'] = 'unknown'
        else:
            recipe['result_name'] = 'Неизвестный предмет'
            recipe['result_icon'] = '❓'

        for ing in recipe['ingredients']:
            if ing['type'] == 'resource':
                conn2 = sqlite3.connect(DB_NAME)
                cur2 = conn2.cursor()
                cur2.execute('SELECT name, icon FROM resource_templates WHERE id = ?', (ing['id'],))
                res = cur2.fetchone()
                conn2.close()
                if res:
                    ing['name'] = res[0]
                    ing['icon'] = res[1]
                else:
                    ing['name'] = 'Неизвестный ресурс'
                    ing['icon'] = '❓'
            elif ing['type'] == 'herb':
                conn2 = sqlite3.connect(DB_NAME)
                cur2 = conn2.cursor()
                cur2.execute('SELECT name, icon FROM herbs WHERE id = ?', (ing['id'],))
                res = cur2.fetchone()
                conn2.close()
                if res:
                    ing['name'] = res[0]
                    ing['icon'] = res[1]
                else:
                    ing['name'] = 'Неизвестная трава'
                    ing['icon'] = '❓'

        recipes.append(recipe)
    return recipes

def craft_item(owner_id, recipe_id):
    print(f"🔧 craft_item вызван для owner_id={owner_id}, recipe_id={recipe_id}")
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute('''
        SELECT result_type, result_id, result_quantity,
               ingredient1_type, ingredient1_id, ingredient1_quantity,
               ingredient2_type, ingredient2_id, ingredient2_quantity,
               ingredient3_type, ingredient3_id, ingredient3_quantity
        FROM craft_recipes WHERE id = ?
    ''', (recipe_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        print("❌ Рецепт не найден")
        return False, "Рецепт не найден."

    if len(row) < 12:
        conn.close()
        print(f"❌ Ошибка структуры БД: ожидается 12 колонок, получено {len(row)}")
        return False, "Ошибка структуры БД. Удалите game.db и перезапустите бота."

    ingredients = []
    for i in range(1, 4):
        base = 3 + (i-1)*3
        ing_type = row[base]
        ing_id = row[base + 1]
        ing_qty = row[base + 2]
        if ing_type and ing_id:
            ingredients.append({'type': ing_type, 'id': ing_id, 'quantity': ing_qty})

    print(f"📦 Ингредиенты: {ingredients}")

    for ing in ingredients:
        if ing['type'] == 'resource':
            cur.execute('SELECT quantity FROM player_resources WHERE owner_id = ? AND resource_id = ?', (owner_id, ing['id']))
            qty = cur.fetchone()
            if not qty or qty[0] < ing['quantity']:
                conn.close()
                return False, f"Недостаточно ресурса (нужно {ing['quantity']})"
        elif ing['type'] == 'herb':
            cur.execute('SELECT quantity FROM player_herbs WHERE owner_id = ? AND herb_id = ?', (owner_id, ing['id']))
            qty = cur.fetchone()
            if not qty or qty[0] < ing['quantity']:
                conn.close()
                return False, f"Недостаточно травы (нужно {ing['quantity']})"

    for ing in ingredients:
        if ing['type'] == 'resource':
            cur.execute('UPDATE player_resources SET quantity = quantity - ? WHERE owner_id = ? AND resource_id = ?',
                       (ing['quantity'], owner_id, ing['id']))
            cur.execute('DELETE FROM player_resources WHERE owner_id = ? AND resource_id = ? AND quantity <= 0',
                       (owner_id, ing['id']))
        elif ing['type'] == 'herb':
            cur.execute('UPDATE player_herbs SET quantity = quantity - ? WHERE owner_id = ? AND herb_id = ?',
                       (ing['quantity'], owner_id, ing['id']))
            cur.execute('DELETE FROM player_herbs WHERE owner_id = ? AND herb_id = ? AND quantity <= 0',
                       (owner_id, ing['id']))

    result_type = row[0]
    result_id = row[1]
    result_qty = row[2]

    if result_type == 'potion':
        cur.execute('INSERT INTO player_consumables (owner_id, consumable_template_id, quantity) VALUES (?, ?, ?) '
                    'ON CONFLICT(owner_id, consumable_template_id) DO UPDATE SET quantity = quantity + ?',
                    (owner_id, result_id, result_qty, result_qty))
    elif result_type == 'item':
        cur.execute('SELECT level FROM characters WHERE id = ?', (owner_id,))
        char_level = cur.fetchone()[0]
        item_level = max(1, char_level // 2)
        cur.execute('INSERT INTO player_items (owner_id, template_id, level, rarity, upgrade_level, quantity) VALUES (?, ?, ?, ?, ?, ?)',
                    (owner_id, result_id, item_level, 1, 0, result_qty))

    conn.commit()
    conn.close()
    print("✅ Крафт успешен")
    return True, "Крафт выполнен успешно!"

def get_craftable_items(owner_id):
    recipes = get_craft_recipes()
    result = []
    for recipe in recipes:
        can_craft = True
        missing = []
        for ing in recipe['ingredients']:
            if ing['type'] == 'resource':
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute('SELECT quantity FROM player_resources WHERE owner_id = ? AND resource_id = ?', (owner_id, ing['id']))
                qty = cur.fetchone()
                conn.close()
                if not qty or qty[0] < ing['quantity']:
                    can_craft = False
                    missing.append(f"{ing.get('name', 'Ресурс')} (есть {qty[0] if qty else 0}/{ing['quantity']})")
            elif ing['type'] == 'herb':
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute('SELECT quantity FROM player_herbs WHERE owner_id = ? AND herb_id = ?', (owner_id, ing['id']))
                qty = cur.fetchone()
                conn.close()
                if not qty or qty[0] < ing['quantity']:
                    can_craft = False
                    missing.append(f"{ing.get('name', 'Трава')} (есть {qty[0] if qty else 0}/{ing['quantity']})")
        result.append({
            'recipe': recipe,
            'can_craft': can_craft,
            'missing': missing
        })
    return result