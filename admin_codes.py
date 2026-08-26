# admin_codes.py
from codes import create_code
from core import send_message
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


async def admin_create_code(vk, user_id):
    """Административная команда для создания кода"""
    # Проверяем, является ли пользователь администратором
    # Здесь нужно добавить вашу проверку на админа
    admin_ids = [31979968]  # ID администраторов
    
    if user_id not in admin_ids:
        await send_message(vk, user_id, '❌ Доступ запрещён.')
        return
    
    # Создаём код
    code = create_code(
        amount=100,          # 100 кристаллов
        expires_days=30,     # действует 30 дней
        max_uses=1,          # одноразовый
        description="Тестовый код 100 кристаллов"
    )
    
    keyboard = VkKeyboard()
    keyboard.add_button('📋 Копировать код', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'copy_code', 'code': code})
    keyboard.add_line()
    keyboard.add_button('🏙️ В город', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_city'})
    
    await send_message(vk, user_id, 
        f'✅ Создан новый промокод:\n\n'
        f'📌 Код: `{code}`\n'
        f'💰 Награда: 100 💎 кристаллов\n'
        f'⏳ Действует: 30 дней\n'
        f'🔄 Одноразовый',
        keyboard)
    