# locations/tavern.py
from core import get_character_async, update_user_async, send_message, get_user_async
from keyboards import get_tavern_keyboard, get_food_keyboard, get_sleep_keyboard, get_back_keyboard, get_sleep_status_keyboard
from scheduler import scheduler

TAVERN_IMAGE = 'photo-240828623_456239032'

async def show_tavern(vk, user_id):
    """Показ таверны"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    await send_message(vk, user_id, '🍺 Таверна «Пьяный тролль». Что желаешь?', get_tavern_keyboard(), attachment=TAVERN_IMAGE)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'city'
    await update_user_async(user_id, state='tavern', context=context)

async def show_tavern_food(vk, user_id):
    """Показ меню еды"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    await send_message(vk, user_id, '🍖 Выберите еду:', get_food_keyboard())
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'tavern'
    await update_user_async(user_id, state='tavern_food', context=context)

async def show_tavern_room(vk, user_id):
    """Показ комнаты"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    await send_message(vk, user_id, '🛏 Выберите, сколько спать:', get_sleep_keyboard())
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'tavern'
    await update_user_async(user_id, state='tavern_room', context=context)

async def restore_after_sleep(vk, user_id, percent):
    """Восстановление после сна"""
    import sqlite3
    from core import get_character_async, update_user_async, send_message, DB_NAME
    char = await get_character_async(user_id)
    if not char:
        return
    max_hp = char['max_hp']
    max_mana = char['max_mana']
    max_stamina = char['max_stamina']
    restore_hp = int(max_hp * percent / 100)
    restore_mana = int(max_mana * percent / 100)
    restore_stamina = int(max_stamina * percent / 100)
    new_hp = min(max_hp, char['hp'] + restore_hp)
    new_mana = min(max_mana, char['mana'] + restore_mana)
    new_stamina = min(max_stamina, char['stamina'] + restore_stamina)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE characters SET hp = ?, mana = ?, stamina = ? WHERE id = ?', 
                (new_hp, new_mana, new_stamina, char['id']))
    conn.commit()
    conn.close()
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context.pop('sleep_task_id', None)
    context.pop('sleep_end_time', None)
    await update_user_async(user_id, context=context)
    await send_message(vk, user_id,
        f'😴 Просыпайтесь! Вы восстановили:\n❤️ {restore_hp} HP\n💧 {restore_mana} MP\n⚡ {restore_stamina} Stamina',
        get_back_keyboard('таверну'))
    await show_tavern(vk, user_id)