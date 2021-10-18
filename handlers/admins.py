import traceback
import asyncio
from asyncio import QueueEmpty
from config import que
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, Chat, CallbackQuery

from cache.admins import admins
from helpers.channelmusic import get_chat_id
from helpers.decorators import authorized_users_only, errors
from helpers.filters import command, other_filters
from callsmusic import callsmusic
from callsmusic.queues import queues
from config import BOT_USERNAME


@Client.on_message(command(["reload", f"reload@{BOT_USERNAME}"]))
@authorized_users_only
async def update_admin(client, message):
    global admins
    new_admins = []
    new_ads = await client.get_chat_members(message.chat.id, filter="administrators")
    for u in new_ads:
        new_admins.append(u.user.id)
    admins[message.chat.id] = new_admins
    await client.send_message(message.chat.id, "✅ Bot **reloaded correctly!**\n\n• The **Admin list** has been **updated.**")


@Client.on_message(command(["pause", f"pause@{BOT_USERNAME}"]) & other_filters)
@errors
@authorized_users_only
async def pause(client, message):
    chat_id = get_chat_id(message.chat)
    if (chat_id not in callsmusic.pytgcalls.active_calls) or (
        callsmusic.pytgcalls.active_calls[chat_id] == "paused"
        await message.reply_text("eweh anjg")
    ):
    else:
        callsmusic.pytgcalls.pause_stream(chat_id)
        await client.send_message("▶️ **Music paused!**\n\n• To resume music playback, use **command » /resume**")


@Client.on_message(command(["resume", f"resume@{BOT_USERNAME}"]) & other_filters)
@errors
@authorized_users_only
async def resume(client, message):
    chat_id = get_chat_id(message.chat)
    if (chat_id not in callsmusic.pytgcalls.active_calls) or (
        callsmusic.pytgcalls.active_calls[chat_id] == "playing"
        await message.reply_text("eweh anjg")
    ):
    else:
        callsmusic.pytgcalls.resume_stream(chat_id)
        await client.send_message("⏸ **Music resumed!**\n\n• To pause music playback, use **command » /pause**")


@Client.on_message(command(["end", f"end@{BOT_USERNAME}"]) & other_filters)
@errors
@authorized_users_only
async def stop(client, message):
    chat_id = get_chat_id(message.chat)
    if chat_id not in callsmusic.pytgcalls.active_calls:
        await message.reply_text("eweh anjg")
    else:
        try:
            queues.clear(chat_id)
        except QueueEmpty:
            pass

        callsmusic.pytgcalls.leave_group_call(chat_id)
        await client.send_message("✅ __The **Userbot has disconnected from voice chat**__")


@Client.on_message(command("skip") & other_filters)
@errors
@authorized_users_only
async def skip(client, message):
    global que
    chat_id = get_chat_id(message.chat)
    if chat_id not in callsmusic.pytgcalls.active_calls:
        await message.reply_text("eweh anjg")
    else:
        queues.task_done(chat_id)

        if queues.is_empty(chat_id):
            callsmusic.pytgcalls.leave_group_call(chat_id)
        else:
            callsmusic.pytgcalls.change_stream(
                chat_id, queues.get(chat_id)["file"]
            )

    qeue = que.get(chat_id)
    if qeue:
        skip = qeue.pop(0)
    if not qeue:
        return
    await client.send_message(f"⏭️ **__You've skipped to the next song__**")
