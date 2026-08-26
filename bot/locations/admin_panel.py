# locations/admin_panel.py
from core import get_character_async, send_message, update_user_async
from keyboards import get_back_keyboard
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from admin import is_admin, admin_codes_menu, admin_show_codes, admin_create_code

async def show_admin_panel(vk, user_id):
    """Показ админ-панели"""
    if not await is_admin(user_id):
        await send_message(vk, user_id, '❌ У вас нет прав администратора.', get_back_keyboard('город'))
        return
    
    keyboard = VkKeyboard()
    keyboard.add_button('📋 Промокоды', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'admin_codes'})
    keyboard.add_line()
    keybokeyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    
    text = f"🛠️ Админ-панель\n\nДобро пожаловать, администратор!"
    
    await send_message(vk, user_id, text, keyboard)
    await update_user_async(user_id, state='admin_panel', context={'parent_state': 'city'})