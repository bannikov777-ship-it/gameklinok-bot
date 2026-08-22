# handlers/mail.py
import sqlite3
from core import get_character_async, update_user_async, send_message, DB_NAME
from mail import get_mail, mark_mail_as_read, delete_mail, claim_attachment, send_mail_with_attachment
from keyboards import get_back_keyboard
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

async def show_mail(vk, user_id):
    """Показ почты"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    mail_list = get_mail(char['id'])
    if not mail_list:
        await send_message(vk, user_id, '📭 У вас нет писем.', get_back_keyboard('профиль'))
        return
    text = "📬 Ваши письма:\n\n"
    keyboard = VkKeyboard()
    for m in mail_list:
        status = "📩" if m['is_read'] else "🆕"
        att_icon = " 📎" if m['attachment_type'] else ""
        text += f"{status} {m['created_at']} от {m['sender_name']}: {m['subject']}{att_icon}\n"
        keyboard.add_button(f"📖 {m['subject'][:15]}", color=VkKeyboardColor.PRIMARY, 
                            payload={'cmd': 'mail_read', 'mail_id': m['id']})
        keyboard.add_line()
    keyboard.add_button('📝 Написать письмо', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'mail_write'})
    keyboard.add_line()
    keyboard.add_button('🔙 Назад в профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'back'})
    await send_message(vk, user_id, text, keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'profile'
    await update_user_async(user_id, state='mail', context=context)


async def show_mail_read(vk, user_id, mail_id):
    """Чтение письма"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    mark_mail_as_read(mail_id, char['id'])
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''SELECT m.subject, m.body, m.created_at, c.name as sender_name,
                          m.attachment_type, m.attachment_id, m.attachment_quantity, m.attachment_silver
                   FROM mail m JOIN characters c ON m.sender_id = c.id
                   WHERE m.id = ? AND m.recipient_id = ?''', (mail_id, char['id']))
    row = cur.fetchone()
    conn.close()
    if not row:
        await send_message(vk, user_id, 'Письмо не найдено.', get_back_keyboard('почту'))
        return
    subject, body, created_at, sender_name, att_type, att_id, att_qty, att_silver = row
    text = f"📩 От: {sender_name}\n📅 {created_at}\n📌 {subject}\n\n{body}"
    if att_type:
        if att_type == 'money':
            text += f"\n💰 Вложение: {att_silver} серебра"
        elif att_type in ('item', 'consumable'):
            text += f"\n📎 Вложение: предмет x{att_qty}"
    keyboard = VkKeyboard()
    if att_type and att_type != 'money':
        keyboard.add_button('📥 Забрать вложение', color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'mail_claim_attachment', 'mail_id': mail_id})
        keyboard.add_line()
    keyboard.add_button('🗑 Удалить', color=VkKeyboardColor.NEGATIVE, payload={'cmd': 'mail_delete', 'mail_id': mail_id})
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'back'})
    await send_message(vk, user_id, text, keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'mail'
    await update_user_async(user_id, state='mail_read', context=context)


async def show_mail_delete(vk, user_id, mail_id):
    """Удаление письма"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    delete_mail(mail_id, char['id'])
    await send_message(vk, user_id, '✅ Письмо удалено.', get_back_keyboard('почту'))
    await show_mail(vk, user_id)


async def show_mail_write(vk, user_id):
    """Написание письма"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    await send_message(vk, user_id, '📝 Введите имя получателя (напишите в чат):')
    await update_user_async(user_id, state='awaiting_mail_recipient', context={'parent_state': 'mail'})


async def show_mail_claim_attachment(vk, user_id, mail_id):
    """Получение вложения из письма"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    success, msg = claim_attachment(mail_id, char['id'])
    if success:
        await send_message(vk, user_id, f'✅ {msg}', get_back_keyboard('почту'))
    else:
        await send_message(vk, user_id, f'❌ {msg}', get_back_keyboard('почту'))
    await show_mail(vk, user_id)


async def show_mail_attachment_menu(vk, user_id):
    """Меню вложения"""
    keyboard = VkKeyboard()
    keyboard.add_button('💰 Деньги', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'mail_attach_money'})
    keyboard.add_button('🗡️ Предметы', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'mail_attach_item'})
    keyboard.add_button('🧪 Расходники', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'mail_attach_consumable'})
    keyboard.add_line()
    keyboard.add_button('📝 Без вложения', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'mail_attach_none'})
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'back'})
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['mail_attachment_type'] = None
    context['mail_attachment_id'] = None
    context['mail_attachment_qty'] = 0
    await update_user_async(user_id, context=context)
    await send_message(vk, user_id, '📎 Выберите тип вложения:', keyboard)


async def show_mail_attach_money(vk, user_id):
    """Прикрепление денег к письму"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    await send_message(vk, user_id, f'Введите сумму серебра для отправки (доступно: {char["silver"]}):')
    await update_user_async(user_id, state='awaiting_mail_attach_money', context={'parent_state': 'mail'})


async def show_mail_attach_item(vk, user_id):
    """Прикрепление предмета к письму"""
    from items import get_player_items
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    items = get_player_items(char['id'])
    if not items:
        await send_message(vk, user_id, 'У вас нет предметов для отправки.', get_back_keyboard('почту'))
        return
    keyboard = VkKeyboard()
    for item in items:
        label = f"{item['icon']} {item['name']} (x{item['quantity']})"
        keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'mail_attach_item_select', 'item_id': item['id']})
        keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'mail_attachment_menu'})
    await send_message(vk, user_id, 'Выберите предмет для отправки:', keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'mail_attachment_menu'
    await update_user_async(user_id, state='mail_attach_item_select', context=context)


async def show_mail_attach_consumable(vk, user_id):
    """Прикрепление расходника к письму"""
    from core import get_player_consumables
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    consumables = get_player_consumables(char['id'])
    if not consumables:
        await send_message(vk, user_id, 'У вас нет расходников для отправки.', get_back_keyboard('почту'))
        return
    keyboard = VkKeyboard()
    for c in consumables:
        label = f"{c['icon']} {c['name']} (x{c['quantity']})"
        keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'mail_attach_consumable_select', 'item_id': c['id']})
        keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'mail_attachment_menu'})
    await send_message(vk, user_id, 'Выберите расходник для отправки:', keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'mail_attachment_menu'
    await update_user_async(user_id, state='mail_attach_consumable_select', context=context)


async def show_mail_attach_quantity(vk, user_id, item_id, item_type):
    """Выбор количества для вложения"""
    import sqlite3
    from core import DB_NAME
    char = await get_character_async(user_id)
    if not char:
        return
    if item_type == 'item':
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('SELECT quantity FROM player_items WHERE id = ? AND owner_id = ?', (item_id, char['id']))
        row = cur.fetchone()
        conn.close()
        max_qty = row[0] if row else 0
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('SELECT quantity FROM player_consumables WHERE id = ? AND owner_id = ?', (item_id, char['id']))
        row = cur.fetchone()
        conn.close()
        max_qty = row[0] if row else 0
    if max_qty <= 0:
        await send_message(vk, user_id, 'У вас нет этого предмета.', get_back_keyboard('почту'))
        return
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['mail_attachment_id'] = item_id
    context['mail_attachment_type'] = 'item' if item_type == 'item' else 'consumable'
    context['mail_attachment_max'] = max_qty
    await update_user_async(user_id, state='awaiting_mail_attach_qty', context=context)
    await send_message(vk, user_id, f'Введите количество (доступно {max_qty} шт.):')


async def show_mail_attach_none(vk, user_id):
    """Отправка письма без вложения"""
    user_data = await get_user_async(user_id)
    context = user_data['context']
    body = context.get('mail_body')
    if body:
        from locations.mail import show_mail_send_with_attachment
        await show_mail_send_with_attachment(vk, user_id, body)
    else:
        await send_message(vk, user_id, 'Ошибка: тело письма не найдено.', get_back_keyboard('почту'))