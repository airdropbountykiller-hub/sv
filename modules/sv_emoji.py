#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Emoji Module
Clean Unicode emoji definitions for Windows compatibility
"""

# Clean emoji definitions using Unicode codes (Windows-safe)
EMOJI = {
    # Basic emojis
    'sunrise': '\U0001F305',          # 🌅
    'sun': '\U0001F31E',              # 🌞
    'night': '\U0001F319',            # 🌙
    'world': '\U0001F30D',            # 🌍
    'globe': '\U0001F30D',            # 🌍
    'earth_americas': '\U0001F30E',   # 🌎
    'earth_asia': '\U0001F30F',       # 🌏
    
    # Finance
    'money': '\U0001F4B0',            # 💰
    'chart': '\U0001F4CA',            # 📊
    'chart_up': '\U0001F4C8',         # 📈
    'chart_down': '\U0001F4C9',       # 📉
    'bank': '\U0001F3E6',             # 🏦
    'dollar': '\U0001F4B2',           # 💲
    'credit_card': '\U0001F4B3',      # 💳
    'btc': '\u20BF',                  # ₿
    'trophy': '\U0001F3C6',           # 🏆
    'medal': '\U0001F3C5',            # 🏅
    
    # Communication
    'calendar': '\U0001F4C5',         # 📅
    'calendar_spiral': '\U0001F5D3',  # 🗓
    'news': '\U0001F4F0',             # 📰
    'link': '\U0001F517',             # 🔗
    'book': '\U0001F4D6',             # 📖
    'notebook': '\U0001F4D3',         # 📓
    'envelope': '\U0001F4E9',         # 📩
    'telephone': '\U0001F4DE',        # 📞
    
    # Objects
    'laptop': '\U0001F4BB',           # 💻
    'folder': '\U0001F4C2',           # 📂
    'file': '\U0001F4C4',             # 📄
    'magnifying_glass': '\U0001F50D', # 🔍
    'lock': '\U0001F512',             # 🔒
    'key': '\U0001F511',              # 🔑
    'tools': '\U0001F6E0\uFE0F',      # 🛠️
    'gear': '\u2699\uFE0F',           # ⚙️
    
    # Status
    'fire': '\U0001F525',             # 🔥
    'warning': '\U0001F6A8',          # 🚨
    'lightning': '\u26A1',            # ⚡
    'info': '\u2139\uFE0F',           # ℹ️
    'check': '\u2705',                # ✅
    'cross': '\u274C',                # ❌
    'warn': '\u26A0\uFE0F',           # ⚠️
    'star': '\u2B50',                 # ⭐
    'red_circle': '\U0001F534',       # 🔴
    'green_circle': '\U0001F7E2',     # 🟢
    'blue_circle': '\U0001F535',      # 🔵
    
    # People
    'brain': '\U0001F9E0',            # 🧠
    'robot': '\U0001F916',            # 🤖
    'person': '\U0001F464',           # 👤
    'eagle': '\U0001F985',            # 🦅
    'speaking_head': '\U0001F5E3',    # 🗣
    'world_map': '\U0001F5FA\uFE0F',     # 🗺️
    
    # Symbols
    'bullet': '\u2022',               # •
    'line': '-',                      # ASCII hyphen for wide compatibility
    'equals': '\u003D',               # =
    'right_arrow': '\u27A1\uFE0F',    # ➡️
    'up_arrow': '\u2B06\uFE0F',       # ⬆️
    'down_arrow': '\u2B07\uFE0F',     # ⬇️
    'back': '\U0001F519',             # 🔙
    'crystal_ball': '\U0001F52E',     # 🔮
    'target': '\U0001F3AF',           # 🎯
    'shield': '\U0001F6E1\uFE0F',     # 🛡️
    'bulb': '\U0001F4A1',             # 💡
    'clock': '\u23F0',                # ⏰
    'compass': '\U0001F9ED',          # 🧭
    'thinking': '\U0001F914',         # 🤔
    'clipboard': '\U0001F4CB',        # 📋
    'magnifier': '\U0001F50D',        # 🔍
    'bar_chart': '\U0001F4CA',        # 📊
    'rocket': '\U0001F680',           # 🚀
    'bear': '\U0001F43B',             # 🐻
    'balance': '\u2696\uFE0F',        # ⚖️
    
    # Country flags
    'us_flag': '\U0001F1FA\U0001F1F8',  # 🇺🇸
    'us': '\U0001F1FA\U0001F1F8',       # 🇺🇸
    'eu_flag': '\U0001F1EA\U0001F1FA',  # 🇪🇺
    'eu': '\U0001F1EA\U0001F1FA',       # 🇪🇺
    'uk_flag': '\U0001F1EC\U0001F1E7',  # 🇬🇧
    'jp_flag': '\U0001F1EF\U0001F1F5',  # 🇯🇵
    'cn_flag': '\U0001F1E8\U0001F1F3',  # 🇨🇳
    'de_flag': '\U0001F1E9\U0001F1EA',  # 🇩🇪
    'fr_flag': '\U0001F1EB\U0001F1F7',  # 🇫🇷
    'world_flag': '\U0001F30D',         # 🌍
}

def get_emoji(name):
    """Get emoji by name, returns empty string if not found."""
    return EMOJI.get(name, '')

def render_emoji(text, emoji_map=None):
    """Renders a string with {emoji_name} placeholders."""
    if emoji_map is None:
        emoji_map = EMOJI
    
    # Replace {emoji_name} with actual emoji
    for name, code in emoji_map.items():
        placeholder = '{' + name + '}'
        text = text.replace(placeholder, code)
    
    return text

# Test emoji rendering if run directly
if __name__ == "__main__":
    test_string = "Today's {sun} report: {chart_up} {btc} {brain}"
    print(render_emoji(test_string))
    
    # Print all available emoji with names
    print("\nAvailable emoji:")
    for name, code in sorted(EMOJI.items()):
        print(f"{code} : {name}")