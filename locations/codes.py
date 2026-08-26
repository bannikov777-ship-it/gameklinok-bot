# locations/codes.py
from core import get_character_async, send_message, update_user_async
from keyboards import get_back_keyboard
from codes import use_code
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

async def show_codes_menu(vk, user_id):
    """Показ меню промокодов"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    keyboard = VkKeyboard()
    keyboard.add_button('🎁 Ввести промокод', color=VkKeyboardColor.PRIMARY, payload={'cmd': 'code_enter'})
    keyboard.add_line()
    keyboard.add_button('👤 В профиль', color=VkKeyboardColor.SECONDARY, payload={'cmd': 'go_profile'})  # ✅ исправлено
    
    text = f"🎁 Промокоды\n\n"
    text += "Введите промокод и получите награду!\n"
    text += f"Ваши 💰: {char.get('silver', 0)}\n"
    text += f"Ваши 💎: {char.get('crystals', 0)}"
    
    await send_message(vk, user_id, text, keyboard)
    await update_user_async(user_id, state='codes', context={'parent_state': 'profile'})  # ✅ исправлено

async def process_code_enter(vk, user_id, code):
    """Обработка ввода промокода"""
    char = await get_character_async(user_id)
    if not char:
        await send_message(vk, user_id, 'Сначала создайте персонажа.', get_back_keyboard('город'))
        return
    
    try:
        result = use_code(char['id'], code.strip())
        print(f"🔍 use_code вернула: {result}")
        
        if isinstance(result, tuple) and len(result) == 4:
            success, msg, amount, reward_type = result
            
            if success:
                char = await get_character_async(user_id)
                reward_icon = '💰' if reward_type == 'silver' else '💎'
                reward_name = 'серебра' if reward_type == 'silver' else 'кристаллов'
                
                await send_message(
                    vk, 
                    user_id, 
                    f'✅ {msg}\n\n'
                    f'Ваши текущие средства:\n'
                    f'💰 Серебро: {char.get("silver", 0)}\n'
                    f'💎 Кристаллы: {char.get("crystals", 0)}',
                    get_back_keyboard('профиль')  # ✅ исправлено
                )
                await update_user_async(user_id, state='profile', context={})
            else:
                await send_message(vk, user_id, f'❌ {msg}', get_back_keyboard('профиль'))  # ✅ исправлено
                await show_codes_menu(vk, user_id)
        
        elif isinstance(result, tuple) and len(result) == 3:
            success, msg, reward = result
            
            if success:
                char = await get_character_async(user_id)
                reward_text = ""
                if reward and isinstance(reward, dict):
                    if reward.get('crystals'):
                        reward_text += f"💎 +{reward['crystals']} кристаллов "
                    if reward.get('silver'):
                        reward_text += f"💰 +{reward['silver']} серебра "
                
                await send_message(
                    vk, 
                    user_id, 
                    f'✅ {msg}\n{reward_text}\n\n'
                    f'💰 Серебро: {char.get("silver", 0)}\n'
                    f'💎 Кристаллы: {char.get("crystals", 0)}',
                    get_back_keyboard('профиль')  # ✅ исправлено
                )
                await update_user_async(user_id, state='profile', context={})
            else:
                await send_message(vk, user_id, f'❌ {msg}', get_back_keyboard('профиль'))  # ✅ исправлено
                await show_codes_menu(vk, user_id)
        
        elif isinstance(result, tuple) and len(result) == 2:
            success, msg = result
            
            if success:
                char = await get_character_async(user_id)
                await send_message(
                    vk, 
                    user_id, 
                    f'✅ {msg}\n\n'
                    f'💰 Серебро: {char.get("silver", 0)}\n'
                    f'💎 Кристаллы: {char.get("crystals", 0)}',
                    get_back_keyboard('профиль')  # ✅ исправлено
                )
                await update_user_async(user_id, state='profile', context={})
            else:
                await send_message(vk, user_id, f'❌ {msg}', get_back_keyboard('профиль'))  # ✅ исправлено
                await show_codes_menu(vk, user_id)
        
        else:
            await send_message(vk, user_id, f'❌ Ошибка: неожиданный формат ответа: {result}', get_back_keyboard('профиль'))
            
    except Exception as e:
        print(f"❌ Ошибка при использовании промокода: {e}")
        import traceback
        traceback.print_exc()
        await send_message(vk, user_id, f'❌ Ошибка при активации промокода. Попробуйте позже.', get_back_keyboard('профиль'))