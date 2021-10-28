"""
MIT License
Copyright (C) 2021 KennedyXMusic
This file is part of https://github.com/KennedyProject/KennedyXMusic
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


from time import time
from datetime import datetime
from config import BOT_USERNAME, BOT_NAME, ASSISTANT_NAME, OWNER_NAME, UPDATES_CHANNEL, GROUP_SUPPORT, UPSTREAM_REPO
from helpers.filters import command
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helpers.decorators import sudo_users_only, authorized_users_only


START_TIME = datetime.utcnow()
START_TIME_ISO = START_TIME.replace(microsecond=0).isoformat()
TIME_DURATION_UNITS = (
    ("week", 60 * 60 * 24 * 7),
    ("days", 60 * 60 * 24),
    ("h", 60 * 60),
    ("m", 60),
    ("s", 1)
)

async def _human_time_duration(seconds):
    if seconds == 0:
        return 'inf'
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append('{} {}{}'
                         .format(amount, unit, "" if amount == 1 else "s"))
    return ', '.join(parts)


@Client.on_message(command("start") & filters.private & ~filters.edited)
async def start_(client: Client, message: Message):
    await message.reply_text(
        f"""<b>✨ Welcome {message.from_user.mention()}!</b>

**💭 [{BOT_NAME}](https://t.me/{GROUP_SUPPORT}) allows you to play music on groups through the new Telegram's voice chats!**

💡 Find out all the **Bot's commands** and how they work by clicking on the **» 📚 Commands** button!""",
        reply_markup=InlineKeyboardMarkup(
            [ 
                [
                    InlineKeyboardButton(
                        "➕ Add me to your group ➕", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
                ],[
                    InlineKeyboardButton(
                        "📚 Command​​", callback_data="cbhelp"
                    ),
                    InlineKeyboardButton(
                        "❤️ Donate", url=f"https://t.me/{OWNER_NAME}")
                ],[
                    InlineKeyboardButton(
                        "👥 Official Group​​", url=f"https://t.me/{GROUP_SUPPORT}"
                    ),
                    InlineKeyboardButton(
                        "📣 Official Channel", url=f"https://t.me/{UPDATES_CHANNEL}")
                ],[
                    InlineKeyboardButton(
                        "🌐 Source Code", url=f"{UPSTREAM_REPO}")
                ],[
                    InlineKeyboardButton(
                        "❔ About me​​", callback_data="cbabout"
                    )
                ]
            ]
        ),
     disable_web_page_preview=True
    )


@Client.on_message(command(["start", f"start@{BOT_USERNAME}"]) & filters.group & ~filters.edited)
async def start(client: Client, message: Message):
    start = time()
    current_time = datetime.utcnow()
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime = await _human_time_duration(int(uptime_sec))
    delta_ping = time() - start
    await message.reply_text(
        f"""<b>👋 **Hello {message.from_user.mention()}** ❗</b>

✅ **I'm active and ready to play music!
• Start time: `{START_TIME_ISO}`
""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Group support", url=f"https://t.me/{GROUP_SUPPORT}"
                    )
                ]
            ]
        )
    )


async def kontol(client: Client, message: Message):
    await message.reply_text("**Bijimane caranya komsol**")


@Client.on_message(command(["help", f"help@{BOT_USERNAME}"]) & filters.group & ~filters.edited)
async def help(client: Client, message: Message):
    await message.reply_text(
        f"""<b>👋 **Hello** {message.from_user.mention()}</b>

**Please press the button below to read the explanation and see the list of available commands !**

💡 Bot by @{OWNER_NAME}""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=" Hoe to use me ❔", url=f"https://t.me/{BOT_USERNAME}"
                    )
                ]
            ]
        )
    )


@Client.on_message(filters.command(["ping", f"ping@{BOT_USERNAME}"]) & ~filters.edited)
@authorized_users_only
async def ping_pong(client: Client, message: Message):
    start = time()
    m_reply = await message.reply_text("`Pinging...`")
    current_time = datetime.utcnow()
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime = await _human_time_duration(int(uptime_sec))
    delta_ping = time() - start
    await m_reply.edit_text(
        "**Pong !!**\n" 
        f"**Time taken:** `{delta_ping * 1000:.3f} ms`\n"
        f"**Service uptime:** `{uptime}`"
    )


@Client.on_message(command(["uptime", f"uptime@{BOT_USERNAME}"]) & ~filters.edited)
@sudo_users_only
async def get_uptime(client: Client, message: Message):
    current_time = datetime.utcnow()
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime = await _human_time_duration(int(uptime_sec))
    await message.reply_text(
        f"🎵 {BOT_NAME} status:\n"
        f"• **uptime:** `{uptime}`\n"
        f"• **start time:** `{START_TIME_ISO}`"
    )
