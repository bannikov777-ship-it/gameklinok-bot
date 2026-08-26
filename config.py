# config.py
import os

TOKEN = 'vk1.a.tPSwEY7iUAcEj86iTEyro-HgT9QLm02Dlj2e39A4hVlBoioM9tUoBKFFZBg9b0HzHkecsunm4IENvXETwzTM43RFF6--DZSYqdPiJ9CA53O4BzXMMR9hX8I3j2il2VkNXWg_7LQ29WujhDNY6NM4qozkkR3dHaw77o9OPosLZy_JTsDJ3VTNgxmRatkbhlmzCei7Gj9luO5IWW5hhj772Q'
GROUP_ID = 241016336

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'game.db')
print(f"📁 Путь к базе данных: {DB_NAME}")