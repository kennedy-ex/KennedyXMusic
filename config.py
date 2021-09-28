import os
from os import getenv
from dotenv import load_dotenv

if os.path.exists("local.env"):
    load_dotenv("local.env")

load_dotenv()
que = {}
SESSION_NAME = getenv("SESSION_NAME", "session")
BOT_TOKEN = getenv("BOT_TOKEN")
BOT_NAME = getenv("BOT_NAME", "Nao Music")
BG_IMAGE = getenv("BG_IMAGE", "https://telegra.ph/file/0f6f8a8a5ad69fe5ecf3d.png")
AUD_IMG = getenv("AUD_IMG", "https://telegra.ph/file/f09189fdd97a3764a1f7a.jpg")
BOT_IMG = getenv("BOT_IMG", "https://telegra.ph/file/fbffad50c0cff6c9001cf.jpg")
admins = {}
API_ID = int(getenv("API_ID"))
API_HASH = getenv("API_HASH")
BOT_USERNAME = getenv("BOT_USERNAME", "NaostreamBot")
ASSISTANT_NAME = getenv("ASSISTANT_NAME", "crybabyex")
GROUP_SUPPORT = getenv("GROUP_SUPPORT", "kenbotsupport")
UPDATES_CHANNEL = getenv("UPDATES_CHANNEL", "KennedyProject")
OWNER_NAME = getenv("OWNER_NAME", "xgothboi") # isi dengan username kamu tanpa simbol @
DEV_NAME = getenv("DEV_NAME", "Sena")
PMPERMIT = getenv("PMPERMIT", "ENABLE")

DURATION_LIMIT = int(getenv("DURATION_LIMIT", "60"))

COMMAND_PREFIXES = list(getenv("COMMAND_PREFIXES", "/ ! .").split())

SUDO_USERS = list(map(int, getenv("SUDO_USERS").split()))
