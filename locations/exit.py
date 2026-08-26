# locations/exit.py
from core import get_character_async, update_user_async, send_message, get_user_async
from keyboards import get_exit_keyboard

EXIT_IMAGE = 'photo-240828623_456239036'

async def show_exit(vk, user_id):
    """Показ выхода из города (ворота)"""
    text = "🚪 Вы вышли за городские ворота. Куда направимся?"
    await send_message(vk, user_id, text, get_exit_keyboard(), attachment=EXIT_IMAGE)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    context['parent_state'] = 'city'
    await update_user_async(user_id, state='exit', context=context)