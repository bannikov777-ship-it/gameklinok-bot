# handlers/mail.py (полный исправленный файл)
import sqlite3
from core import get_character_async, update_user_async, send_message, DB_NAME, get_user_async, get_character_by_id_async
from mail import get_mail, mark_mail_as_read, delete_mail, claim_attachment, send_mail_with_attachment_by_id
from keyboards import get_back_keyboard, get_mail_keyboard, get_mail_read_keyboard, get_mail_attachment_keyboard
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from items import get_player_items
from core import get_player_consumables


async def show_mail(vk, user_id):
    """Показ почты"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    mail_list = get_mail(char['id'])
    if not mail_list:
        await send_message(vk, user_id, '📭 У вас нет писем.', get_mail_keyboard())
        return
    text = "📬 Ваши письма:\n\n"
    keyboard = VkKeyboard()
    for m in mail_list:
        status = "📩" if m['is_read'] else "🆕"
        att_icon = " 📎" if m['attachment_type'] else ""
        text += f"{status} {m['created_at']} от {m['sender_name']} (ID: {m['sender_id']}): {m['subject']}{att_icon}\n"
        keyboard.add_button(f"📖 {m['subject'][:15]}", color=VkKeyboardColor.PRIMARY, 
                            payload={'cmd': 'mail_read', 'mail_id': m['id']})
        keyboard.add_line()
    keyboard.add_button('📝 Написать письмо', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'mail_write'})
    keyboard.add_line()
    keyboard.add_button('👤 В профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_profile'})
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
    cur.execute('''SELECT m.subject, m.body, m.created_at, c.name as sender_name, c.id as sender_id,
                          m.attachment_type, m.attachment_id, m.attachment_quantity, m.attachment_silver
                   FROM mail m JOIN characters c ON m.sender_id = c.id
                   WHERE m.id = ? AND m.recipient_id = ?''', (mail_id, char['id']))
    row = cur.fetchone()
    conn.close()
    if not row:
        await send_message(vk, user_id, 'Письмо не найдено.', get_back_keyboard('почту'))
        return
    subject, body, created_at, sender_name, sender_id, att_type, att_id, att_qty, att_silver = row
    text = f"📩 От: {sender_name} (ID: {sender_id})\n📅 {created_at}\n📌 {subject}\n\n{body}"
    if att_type:
        if att_type == 'money':
            text += f"\n💰 Вложение: {att_silver} серебра"
        elif att_type in ('item', 'consumable'):
            text += f"\n📎 Вложение: предмет x{att_qty}"
    
    keyboard = VkKeyboard()
    if att_type:
        keyboard.add_button('📥 Забрать вложение', color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'mail_claim_attachment', 'mail_id': mail_id})
        keyboard.add_line()
    keyboard.add_button('🗑 Удалить', color=VkKeyboardColor.NEGATIVE, 
                       payload={'cmd': 'mail_delete', 'mail_id': mail_id})
    keyboard.add_button('📬 На почту', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_profile'})
    
    await send_message(vk, user_id, text, keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'mail'
    context['current_mail_id'] = mail_id
    await update_user_async(user_id, state='mail_read', context=context)


async def show_mail_delete(vk, user_id, mail_id):
    """Удаление письма"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    delete_mail(mail_id, char['id'])
    await send_message(vk, user_id, '✅ Письмо удалено.', get_mail_keyboard())
    await show_mail(vk, user_id)


async def show_mail_write(vk, user_id):
    """Написание письма"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    await send_message(vk, user_id, '📝 Введите ID получателя (число) или имя персонажа:\n(например: 123 или Вася)')
    await update_user_async(user_id, state='awaiting_mail_recipient', context={'parent_state': 'mail'})


async def show_mail_write_subject(vk, user_id, recipient_input):
    """Ввод темы письма"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    try:
        recipient_id = int(recipient_input)
        cur.execute('SELECT id, name FROM characters WHERE id = ?', (recipient_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            await send_message(vk, user_id, f'❌ Игрок с ID {recipient_id} не найден.', get_mail_keyboard())
            return
        recipient_id, recipient_name = row
    except ValueError:
        cur.execute('SELECT id, name FROM characters WHERE name = ?', (recipient_input,))
        row = cur.fetchone()
        if not row:
            conn.close()
            await send_message(vk, user_id, f'❌ Игрок с именем "{recipient_input}" не найден.', get_mail_keyboard())
            return
        recipient_id, recipient_name = row
    
    conn.close()
    
    if recipient_id == char['id']:
        await send_message(vk, user_id, '❌ Нельзя отправить письмо самому себе.', get_mail_keyboard())
        return
    
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['mail_recipient_id'] = recipient_id
    context['mail_recipient_name'] = recipient_name
    await update_user_async(user_id, context=context)
    
    await send_message(vk, user_id, f'📝 Введите тему письма для {recipient_name} (ID: {recipient_id}):')
    await update_user_async(user_id, state='awaiting_mail_subject', context=context)


async def show_mail_write_body(vk, user_id, subject):
    """Ввод тела письма"""
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['mail_subject'] = subject
    await update_user_async(user_id, context=context)
    await send_message(vk, user_id, f'📝 Введите текст письма (тема: {subject}):')
    await update_user_async(user_id, state='awaiting_mail_body', context=context)


async def show_mail_send(vk, user_id, body):
    """Отправка письма (выбор вложения)"""
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['mail_body'] = body
    await update_user_async(user_id, context=context)
    await show_mail_attachment_menu(vk, user_id)


async def show_mail_attachment_menu(vk, user_id):
    """Меню вложения (без расходников)"""
    keyboard = VkKeyboard()
    keyboard.add_button('💰 Деньги', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'mail_attach_money'})
    keyboard.add_button('🗡️ Предметы', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'mail_attach_item'})
    keyboard.add_line()
    keyboard.add_button('📝 Без вложения', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'mail_attach_none'})
    keyboard.add_button('📬 На почту', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_profile'})
    
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['mail_attachment_type'] = None
    context['mail_attachment_id'] = None
    context['mail_attachment_qty'] = 0
    context['mail_attachment_silver'] = 0
    await update_user_async(user_id, state='mail_attachment_menu', context=context)
    await send_message(vk, user_id, '📎 Выберите тип вложения:', keyboard)


async def show_mail_attach_money(vk, user_id):
    """Прикрепление денег к письму"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    user_data = await get_user_async(user_id)
    context = user_data['context']
    
    if not context.get('mail_recipient_id'):
        await send_message(vk, user_id, '❌ Ошибка: получатель не найден. Попробуйте начать заново.', get_mail_keyboard())
        context.pop('mail_recipient_id', None)
        context.pop('mail_subject', None)
        context.pop('mail_body', None)
        await update_user_async(user_id, state='mail', context=context)
        return
    if not context.get('mail_subject'):
        await send_message(vk, user_id, '❌ Ошибка: тема письма не найдена. Попробуйте начать заново.', get_mail_keyboard())
        context.pop('mail_recipient_id', None)
        context.pop('mail_subject', None)
        context.pop('mail_body', None)
        await update_user_async(user_id, state='mail', context=context)
        return
    
    await send_message(vk, user_id, f'Введите сумму серебра для отправки (доступно: {char["silver"]}):')
    await update_user_async(user_id, state='awaiting_mail_attach_money', context=context)


async def show_mail_attach_item(vk, user_id):
    """Прикрепление предмета к письму"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    user_data = await get_user_async(user_id)
    context = user_data['context']
    
    if not context.get('mail_recipient_id'):
        await send_message(vk, user_id, '❌ Ошибка: получатель не найден. Попробуйте начать заново.', get_mail_keyboard())
        context.pop('mail_recipient_id', None)
        context.pop('mail_subject', None)
        context.pop('mail_body', None)
        await update_user_async(user_id, state='mail', context=context)
        return
    if not context.get('mail_subject'):
        await send_message(vk, user_id, '❌ Ошибка: тема письма не найдена. Попробуйте начать заново.', get_mail_keyboard())
        context.pop('mail_recipient_id', None)
        context.pop('mail_subject', None)
        context.pop('mail_body', None)
        await update_user_async(user_id, state='mail', context=context)
        return
    
    items = get_player_items(char['id'])
    if not items:
        await send_message(vk, user_id, 'У вас нет предметов для отправки.', get_mail_attachment_keyboard())
        return
    
    keyboard = VkKeyboard()
    for item in items:
        label = f"{item['icon']} {item['name']} (x{item['quantity']})"
        keyboard.add_button(label, color=VkKeyboardColor.PRIMARY,
                            payload={'cmd': 'mail_attach_item_select', 'item_id': item['id']})
        keyboard.add_line()
    keyboard.add_button('📬 На почту', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_profile'})
    await send_message(vk, user_id, 'Выберите предмет для отправки:', keyboard)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'mail_attachment_menu'
    await update_user_async(user_id, state='mail_attach_item_select', context=context)


async def show_mail_attach_quantity(vk, user_id, item_id, item_type):
    """Выбор количества для вложения"""
    char = await get_character_async(user_id)
    if not char:
        return
    
    user_data = await get_user_async(user_id)
    context = user_data['context']
    
    if not context.get('mail_recipient_id'):
        await send_message(vk, user_id, '❌ Ошибка: получатель не найден. Попробуйте начать заново.', get_mail_keyboard())
        context.pop('mail_recipient_id', None)
        context.pop('mail_subject', None)
        context.pop('mail_body', None)
        await update_user_async(user_id, state='mail', context=context)
        return
    if not context.get('mail_subject'):
        await send_message(vk, user_id, '❌ Ошибка: тема письма не найдена. Попробуйте начать заново.', get_mail_keyboard())
        context.pop('mail_recipient_id', None)
        context.pop('mail_subject', None)
        context.pop('mail_body', None)
        await update_user_async(user_id, state='mail', context=context)
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
        await send_message(vk, user_id, 'У вас нет этого предмета.', get_mail_attachment_keyboard())
        return
    
    context['mail_attachment_id'] = item_id
    context['mail_attachment_type'] = item_type
    context['mail_attachment_max'] = max_qty
    await update_user_async(user_id, context=context)
    await send_message(vk, user_id, f'Введите количество (доступно {max_qty} шт.):')
    await update_user_async(user_id, state='awaiting_mail_attach_qty', context=context)


async def show_mail_attach_none(vk, user_id):
    """Отправка письма без вложения"""
    user_data = await get_user_async(user_id)
    context = user_data['context']
    body = context.get('mail_body')
    if body:
        await show_mail_send_with_attachment(vk, user_id, body)
    else:
        await send_message(vk, user_id, 'Ошибка: тело письма не найдено.', get_mail_attachment_keyboard())


async def show_mail_claim_attachment(vk, user_id, mail_id):
    """Получение вложения из письма"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    success, msg = claim_attachment(mail_id, char['id'])
    if success:
        await send_message(vk, user_id, f'✅ {msg}', get_mail_keyboard())
    else:
        await send_message(vk, user_id, f'❌ {msg}', get_mail_keyboard())
    await show_mail(vk, user_id)


async def show_mail_send_with_attachment(vk, user_id, body):
    """Отправка письма с вложением"""
    user_data = await get_user_async(user_id)
    context = user_data['context']
    recipient_id = context.get('mail_recipient_id')
    recipient_name = context.get('mail_recipient_name')
    subject = context.get('mail_subject')
    att_type = context.get('mail_attachment_type')
    att_id = context.get('mail_attachment_id')
    att_qty = context.get('mail_attachment_qty', 0)
    att_silver = context.get('mail_attachment_silver', 0)
    
    print(f"📨 Отправка письма: recipient_id={recipient_id}, subject={subject}, att_type={att_type}, att_id={att_id}, att_qty={att_qty}, att_silver={att_silver}")
    
    if not recipient_id:
        await send_message(vk, user_id, '❌ Ошибка: не указан получатель. Попробуйте начать заново.', get_mail_keyboard())
        context.pop('mail_recipient_id', None)
        context.pop('mail_subject', None)
        context.pop('mail_attachment_type', None)
        context.pop('mail_body', None)
        await update_user_async(user_id, state='mail', context=context)
        return
    
    if not subject:
        await send_message(vk, user_id, '❌ Ошибка: не указана тема письма. Попробуйте начать заново.', get_mail_keyboard())
        context.pop('mail_recipient_id', None)
        context.pop('mail_subject', None)
        context.pop('mail_attachment_type', None)
        context.pop('mail_body', None)
        await update_user_async(user_id, state='mail', context=context)
        return
    
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    success, msg = send_mail_with_attachment_by_id(
        char['id'], recipient_id, subject, body, 
        att_type, att_id, att_qty, att_silver
    )
    
    if success:
        await send_message(vk, user_id, f'✅ {msg}', get_mail_keyboard())
        context.pop('mail_recipient_id', None)
        context.pop('mail_recipient_name', None)
        context.pop('mail_subject', None)
        context.pop('mail_attachment_type', None)
        context.pop('mail_attachment_id', None)
        context.pop('mail_attachment_qty', None)
        context.pop('mail_attachment_silver', None)
        context.pop('mail_body', None)
        context.pop('mail_attachment_max', None)
        await update_user_async(user_id, state='mail', context=context)
        await show_mail(vk, user_id)
    else:
        await send_message(vk, user_id, f'❌ {msg}', get_mail_keyboard())
        await show_mail(vk, user_id)