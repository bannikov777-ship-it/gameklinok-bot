# core/render.py
from .character import get_item_prefix, get_character_by_id
from .stats import CLASS_BASE_STATS, CLASS_GROWTH, NEUTRAL_STATS, NEUTRAL_GROWTH
from .async_wrappers import get_player_consumables, get_player_herbs
from utils import exp_to_next_level
from resources import get_player_resources

GENDER_IMAGES = {
    'male': 'photo-240828623_456239242',
    'female': 'photo-240828623_456239241'
}

def format_gender(gender):
    if gender == 'male':
        return 'Муж.'
    elif gender == 'female':
        return 'Жен.'
    return gender

def upload_profile_image(vk, user_id, gender):
    return GENDER_IMAGES.get(gender)

def render_profile(char, equipment):
    from vip import get_vip, get_vip_icon, get_vip_name, VIP_NAMES, VIP_COLORS, VIP_BONUSES
    
    slots_display = {'head': '🎩', 'weapon_right': '🗡️', 'armor': '🛡️', 'boots': '👢'}
    
    if char.get('class') and char.get('level', 0) >= 20:
        slots_display['weapon_left'] = '⚔️'
    
    equip_str = []
    for slot_key, icon in slots_display.items():
        if slot_key in equipment and equipment[slot_key]:
            equip_str.append(f"{icon}{equipment[slot_key]['name']}")
        else:
            equip_str.append(f"{icon}—")
    equip_line = " | ".join(equip_str)
    
    exp_current = char['exp']
    exp_needed = exp_to_next_level(char['level'])
    progress = min(1.0, exp_current / exp_needed) if exp_needed > 0 else 0
    bar_length = 10
    filled = int(progress * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    debuff_text = ""
    if char.get('debuff') == 1:
        debuff_text = " ☠️ Проклятие (-30% стат)"
    elif char.get('debuff') == 2:
        debuff_text = " 🔥 Печать башни (-50% стат)"
    
    gender_display = format_gender(char['gender'])
    class_display = char['class'] if char['class'] else "Не выбран"
    
    # VIP отображение
    vip_level, expires_at = get_vip(char['id'])
    vip_display = ""
    vip_bonus_text = ""
    vip_name = ""
    vip_icon = ""
    
    if vip_level > 0:
        vip_icon = VIP_COLORS.get(vip_level, '')
        vip_name = VIP_NAMES.get(vip_level, '')
        vip_display = f" {vip_icon}[{vip_name}]"
        bonus = VIP_BONUSES.get(vip_level, {})
        vip_bonus_text = f"\n👑 VIP бонус: +{bonus.get('exp', 0)}% к опыту и серебру"
    
    # Формируем строку с ID и именем
    id_display = f"🆔 {char['id']}"
    
    left_hand_hint = ""
    if not char.get('class'):
        left_hand_hint = "\n🛡️ Левая рука откроется после выбора класса (20 уровень)"
    
    text = (
        f"👤 {id_display} {char['name']}{vip_display} | {gender_display} | {class_display} | Ур.{char['level']} 📈 Опыт: {exp_current} / {exp_needed} [{bar}]\n"
        f"❤️ {char['hp']}/{char['max_hp']} | 💧 {char['mana']}/{char['max_mana']} | ⚡ {char['stamina']}/{char['max_stamina']}\n"
        f"⚔️ {char['attack']} | 🛡 {char['defense']} | 💥{round(char['crit_chance'])}% | 💨{round(char['dodge_chance'])}% | 🏆 {char.get('trophies', 0)} | 💰 {char['silver']} | 💎 {char.get('crystals', 0)}{vip_bonus_text}\n"
        f"ЭКИПИРОВКА: {equip_line}{debuff_text}{left_hand_hint}"
    )
    return text


# core/render.py - исправленная render_inventory (добавляем VIP статус)

def render_inventory(inv_items, equipment, consumables=None, owner_id=None):
    from .async_wrappers import get_player_consumables, get_player_herbs
    from resources import get_player_resources
    from core import get_character_by_id
    from vip import get_vip, get_vip_icon, get_vip_name, VIP_NAMES, VIP_COLORS
    
    char = None
    if owner_id:
        char = get_character_by_id(owner_id)
    
    lines = []
    
    # VIP статус в инвентаре
    if char:
        vip_level, expires_at = get_vip(char['id'])
        if vip_level > 0:
            vip_icon = VIP_COLORS.get(vip_level, '')
            vip_name = VIP_NAMES.get(vip_level, '')
            lines.append(f"{vip_icon} {char['name']} [{vip_name}]")
            # Показываем оставшееся время
            from datetime import datetime
            if expires_at:
                remaining = datetime.fromisoformat(expires_at) - datetime.now()
                days = remaining.days
                if days > 0:
                    lines.append(f"👑 VIP статус: {vip_name} (действует {days} дн.)")
                else:
                    hours = remaining.seconds // 3600
                    if hours > 0:
                        lines.append(f"👑 VIP статус: {vip_name} (действует {hours} ч.)")
                    else:
                        lines.append(f"👑 VIP статус: {vip_name} (действует менее часа)")
            lines.append("")
    
    slots_info = {
        'head': ('🎩', 'Голова'),
        'weapon_right': ('🗡️', 'Правая рука'),
        'armor': ('🛡️', 'Торс'),
        'boots': ('👢', 'Сапоги')
    }
    
    if char and char.get('class') and char.get('level', 0) >= 20:
        slots_info['weapon_left'] = ('🛡️', 'Левая рука')
    
    def item_bonus_str(item):
        if not item:
            return ""
        bonus = []
        if item.get('attack'): bonus.append(f"+{item['attack']} атк")
        if item.get('defense'): bonus.append(f"+{item['defense']} защ")
        if item.get('hp'): bonus.append(f"+{item['hp']} HP")
        if item.get('mana'): bonus.append(f"+{item['mana']} маны")
        if item.get('bonus_crit'): 
            crit = item['bonus_crit']
            bonus.append(f"💥{crit:+}% крит")
        if item.get('bonus_dodge'): 
            dodge = item['bonus_dodge']
            bonus.append(f"💨{dodge:+}% уворот")
        upgrade = item.get('upgrade_level', 0)
        if upgrade > 0:
            bonus.append(f"🔨+{upgrade}")
        return f" ({', '.join(bonus)})" if bonus else ""
    
    def item_line(item):
        if not item:
            return "—"
        return f"{item['icon']}{item['name']}{item_bonus_str(item)}"

    lines.append(f"{slots_info['head'][0]} {slots_info['head'][1]}")
    lines.append(item_line(equipment.get('head')))
    lines.append("")
    
    right = equipment.get('weapon_right')
    left = equipment.get('weapon_left') if 'weapon_left' in slots_info else None
    
    if left is not None:
        lines.append(f"{slots_info['weapon_right'][0]}{slots_info['weapon_right'][1]}/{slots_info['weapon_left'][0]}{slots_info['weapon_left'][1]}")
        lines.append(f"{item_line(right) if right else '—'} / {item_line(left) if left else '—'}")
    else:
        lines.append(f"{slots_info['weapon_right'][0]}{slots_info['weapon_right'][1]}")
        lines.append(item_line(right) if right else '—')
    lines.append("")
    
    lines.append(f"{slots_info['armor'][0]} {slots_info['armor'][1]}")
    lines.append(item_line(equipment.get('armor')))
    lines.append("")
    
    lines.append(f"{slots_info['boots'][0]} {slots_info['boots'][1]}")
    lines.append(item_line(equipment.get('boots')))
    lines.append("")
    
    if char and (not char.get('class') or char.get('level', 0) < 20):
        lines.append("🛡️ Левая рука откроется после выбора класса (20 уровень)")
        lines.append("")
    
    # Предметы в сумке
    lines.append("🎒 Предметы в сумке:")
    if not inv_items:
        lines.append("пусто")
    else:
        for item in inv_items:
            rarity_icons = {1:'⚪', 2:'🟢', 3:'🔵', 4:'🟣', 5:'🟠'}
            rarity_names = {1:'Обычный', 2:'Необычный', 3:'Редкий', 4:'Эпический', 5:'Легендарный'}
            star = rarity_icons.get(item['rarity'], '⚪') * item['rarity']
            
            bonus = []
            if item['attack']: bonus.append(f"+{item['attack']} атк")
            if item['defense']: bonus.append(f"+{item['defense']} защ")
            if item['hp']: bonus.append(f"+{item['hp']} HP")
            if item['mana']: bonus.append(f"+{item['mana']} маны")
            if item.get('bonus_crit'): 
                crit = item['bonus_crit']
                bonus.append(f"💥{crit:+}% крит")
            if item.get('bonus_dodge'): 
                dodge = item['bonus_dodge']
                bonus.append(f"💨{dodge:+}% уворот")
            upgrade = item.get('upgrade_level', 0)
            if upgrade > 0:
                bonus.append(f"🔨+{upgrade}")
            bonus_str = f" ({', '.join(bonus)})" if bonus else ""
            
            upgrade_star = f" [+{upgrade}]" if upgrade > 0 else ""
            
            # Формат: Иконка Имя (Ур.X) [+заточка] Редкость Бонусы (xКоличество)
            lines.append(f"{item['icon']} {item['name']} (Ур.{item['level']}){upgrade_star} {star} {rarity_names.get(item['rarity'], '')}{bonus_str} (x{item['quantity']})")
    
    # Расходники
    if consumables is None and owner_id:
        consumables = get_player_consumables(owner_id)
    lines.append("")
    lines.append("🧪 Расходники:")
    if consumables:
        for c in consumables:
            lines.append(f"{c['icon']} {c['name']} (x{c['quantity']})")
    else:
        lines.append("пусто")
    
    # Травы
    if owner_id:
        herbs = get_player_herbs(owner_id)
        lines.append("")
        lines.append("🌿 Травы:")
        if herbs:
            for h in herbs:
                lines.append(f"{h['icon']} {h['name']} (x{h['quantity']})")
        else:
            lines.append("пусто")
        
        # Ресурсы
        resources = get_player_resources(owner_id)
        lines.append("")
        lines.append("🎁 Ресурсы (трофеи):")
        if resources:
            for r in resources:
                lines.append(f"{r['icon']} {r['name']} (x{r['quantity']})")
        else:
            lines.append("пусто")
    
    return "\n".join(lines)