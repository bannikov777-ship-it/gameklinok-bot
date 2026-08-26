# locations/profile.py
from core import get_character_async, update_user_async, send_message, render_profile, upload_profile_image, get_character, get_user_async
from items import get_equipped_items
from keyboards import get_profile_keyboard, get_back_keyboard
from .base import navigate_to

async def show_profile(vk, user_id):
    """Показ профиля"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    equipment = get_equipped_items(char['id'])
    profile_text = render_profile(char, equipment)
    if char.get('materials'):
        materials_text = "\n🎒 Материалы: " + ", ".join([f"{k}: {v}" for k, v in char['materials'].items()])
        profile_text += materials_text
    attachment = upload_profile_image(vk, user_id, char['gender'])
    await send_message(vk, user_id, profile_text, get_profile_keyboard(), attachment=attachment)
    user_data = await get_user_async(user_id)
    context = user_data['context']
    current_state = user_data['state']
    if current_state not in ('profile', 'inventory'):
        context['return_to'] = current_state
    await update_user_async(user_id, state='profile', context=context)