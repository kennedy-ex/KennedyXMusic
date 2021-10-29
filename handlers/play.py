import os
import json
import ffmpeg
import aiofiles
import asyncio
import aiohttp
import requests
import converter
from os import path
from asyncio.queues import QueueEmpty
from pyrogram import Client, filters
from typing import Callable
from helpers.channelmusic import get_chat_id
from callsmusic import callsmusic
from callsmusic.queues import queues
from helpers.admins import get_administrators
from youtube_search import YoutubeSearch
from callsmusic.callsmusic import client as USER
from pyrogram.errors import UserAlreadyParticipant
from downloaders import youtube
from config import que, THUMB_IMG, DURATION_LIMIT, BOT_USERNAME, UPDATES_CHANNEL, GROUP_SUPPORT, ASSISTANT_NAME, BOT_NAME
from helpers.chattitle import CHAT_TITLE
from helpers.filters import command, other_filters
from helpers.decorators import authorized_users_only
from helpers.gets import get_file_name, get_url
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, Voice
from cache.admins import admins as a
from PIL import Image, ImageFont, ImageDraw


chat_id = None
useer ="NaN"
DISABLED_GROUPS = []


def cb_admin_check(func: Callable) -> Callable:
    async def decorator(client, cb):
        admemes = a.get(cb.message.chat.id)
        if cb.from_user.id in admemes:
            return await func(client, cb)
        else:
            await cb.answer("💡 only admin can tap this button !", show_alert=True)
            return

    return decorator                                                                       
                                          
                                                                                    
def transcode(filename):
    ffmpeg.input(filename).output(
        "input.raw",
        format="s16le",
        acodec="pcm_s16le",
        ac=2,
        ar="48k"
    ).overwrite_output().run() 
    os.remove(filename)

# Convert seconds to mm:ss
def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)


# Convert hh:mm:ss to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


# Change image size
def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


async def generate_cover(title, thumbnail, ctitle):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open("background.png", mode="wb")
                await f.write(await resp.read())
                await f.close()
    image1 = Image.open("./background.png")
    image2 = Image.open("etc/foreground.png")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save("temp.png")
    img = Image.open("temp.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("etc/WigendaTypewrite.ttf", 46)
    draw.text((30, 543), f"Playing on {ctitle[:10]} ...", (0, 0, 0), font=font)
    font = ImageFont.truetype("etc/Roboto-Medium.ttf", 75)
    draw.text((30, 615),
        f"{title[:20]} ...",
        (0, 0, 0),
        font=font,
    )
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")


@Client.on_callback_query(
    filters.regex(pattern=r"^(closed)$")
)
@cb_admin_check
async def bt_cls(b, cb):
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    if type_ == "closed":
        await cb.answer("Closed Thumbnail")
        await cb.message.delete()


@Client.on_message(command(["playlist", f"playlist@{BOT_USERNAME}"]) & filters.group & ~filters.edited)
async def playlist(client, message):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🗑️ Close", callback_data="closed"
                ),
            ]
        ]
    )

    global que
    if message.chat.id in DISABLED_GROUPS:
        return
    queue = que.get(message.chat.id)
    if not queue:
        await message.reply_text("**nothing in streaming !**")
    temp = []
    for t in queue:
        temp.append(t)
    now_playing = temp[0][0]
    by = temp[0][1].mention(style="md")
    msg = "🎵 **Now playing** on {}".format(message.chat.title)
    msg += "\n• "+ now_playing
    msg += "\n• Req By "+by
    temp.pop(0)
    if temp:
        msg += "\n\n"
        msg += "**Queued Song**"
        for song in temp:
            name = song[0]
            usr = song[1].mention(style="md")
            msg += f"\n• {name}"
            msg += f"\n• Req by {usr}\n"
    await message.reply_text(msg, reply_markup=keyboard)
                            
# ============================= Settings =========================================
def updated_stats(chat, queue, vol=100):
    if chat.id in callsmusic.pytgcalls.active_calls:
        stats = "⚙️ Settings from **{}**".format(chat.title)
        if len(que) > 0:
            stats += "\n\n"
            stats += "🎚️ Volume: {}%\n".format(vol)
            stats += "🎼 Song in queue: `{}`\n".format(len(que))
            stats += "💡 Now playing: **{}**\n".format(queue[0][0])
            stats += "🎧 Requested by: {}".format(queue[0][1].mention)
    else:
        stats = None
    return stats

def r_ply(type_):
    if type_ == "play":
        pass
    else:
        pass
    mar = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏹", "leave"),
                InlineKeyboardButton("⏸", "puse"),
                InlineKeyboardButton("▶️", "resume"),
                InlineKeyboardButton("⏭", "skip")
            ],
            [
                InlineKeyboardButton("📖 Playlist", "playlist"),
            ],
            [       
                InlineKeyboardButton("🗑 Close", "cls")
            ]        
        ]
    )
    return mar


@Client.on_message(command(["player", f"player@{BOT_USERNAME}"]) & filters.group & ~filters.edited)
@authorized_users_only
async def settings(client, message):
    playing = None
    if message.chat.id in callsmusic.pytgcalls.active_calls:
        playing = True
    queue = que.get(message.chat.id)
    stats = updated_stats(message.chat, queue)
    if stats:
        if playing:
            await message.reply(stats, reply_markup=r_ply("pause"))
            
        else:
            await message.reply(stats, reply_markup=r_ply("play"))
    else:
        await message.reply("❌ **Nothing is currently playing**")


@Client.on_message(
    command(["musicplayer", f"musicplayer@{BOT_USERNAME}"]) & ~filters.edited & ~filters.bot & ~filters.private
)
@authorized_users_only
async def hfmm(_, message):
    global DISABLED_GROUPS
    try:
        user_id = message.from_user.id
    except:
        return
    if len(message.command) != 2:
        await message.reply_text(
            "**i'm only know** `/musicplayer on` **and** `/musicplayer off`"
        )
        return
    status = message.text.split(None, 1)[1]
    message.chat.id
    if status == "ON" or status == "on" or status == "On":
        lel = await message.reply("`processing...`")
        if not message.chat.id in DISABLED_GROUPS:
            await lel.edit("**music player already activated.**")
            return
        DISABLED_GROUPS.remove(message.chat.id)
        await lel.edit(
            f"💡 **music player has been activated in this chat.**\n\n☁️ `{message.chat.id}`"
        )

    elif status == "OFF" or status == "off" or status == "Off":
        lel = await message.reply("`processing...`")
        
        if message.chat.id in DISABLED_GROUPS:
            await lel.edit("**music player already deactivated.**")
            return
        DISABLED_GROUPS.append(message.chat.id)
        await lel.edit(
            f"💡 **music player has been deactivated in this chat.**\n\n☁️ `{message.chat.id}`"
        )
    else:
        await message.reply_text(
            "**i'm only know** `/musicplayer on` **and** `/musicplayer off`"
        )


@Client.on_callback_query(filters.regex(pattern=r"^(playlist)$"))
async def p_cb(b, cb):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔙 Back", callback_data="menu")
            ],
        ]
    )

    global que    
    que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    cb.message.chat
    cb.message.reply_markup.inline_keyboard[0][0].callback_data
    if type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("**nothing is playing !**")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**Now playing** in {}".format(cb.message.chat.title)
        msg += "\n• " + now_playing
        msg += "\n• Req by " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**Queued Song**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n• {name}"
                msg += f"\n• Req by {usr}\n"
        await cb.message.edit(msg, reply_markup=keyboard)


@Client.on_callback_query(
    filters.regex(pattern=r"^(play|pause|skip|leave|puse|resume|menu|cls)$")
)
@cb_admin_check
async def m_cb(b, cb):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔙 Back", callback_data="menu")
            ],
        ]
    )

    global que
    if (
        cb.message.chat.title.startswith("Channel Music: ")
        and chat.title[14:].isnumeric()
    ):
        chet_id = int(chat.title[13:])
    else:
        chet_id = cb.message.chat.id
    qeue = que.get(chet_id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    m_chat = cb.message.chat

    the_data = cb.message.reply_markup.inline_keyboard[0][0].callback_data
    if type_ == "pause":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "paused"
        ):
            await cb.answer(
                "assistant is not connected to voice chat !", show_alert=True
            )
        else:
            callsmusic.pytgcalls.pause_stream(chet_id)

            await cb.answer("music paused")
            await cb.message.edit(
                updated_stats(m_chat, qeue), reply_markup=r_ply("play")
            )

    elif type_ == "play":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "playing"
        ):
            await cb.answer(
                "assistant is not connected to voice chat !", show_alert=True
            )
        else:
            callsmusic.pytgcalls.resume_stream(chet_id)
            await cb.answer("music resumed")
            await cb.message.edit(
                updated_stats(m_chat, qeue), reply_markup=r_ply("pause")
            )

    elif type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("❌ **no music is currently playing**")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "💡 **now playing** on {}".format(cb.message.chat.title)
        msg += "\n• " + now_playing
        msg += "\n• Req by " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**Queued Song:**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n\n• {name}"
                msg += f"\n• Req by {usr}"
        await cb.message.edit(msg, reply_markup=keyboard)

    elif type_ == "resume":
        psn = "▶ music playback has resumed"
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "playing"
        ):
            await cb.answer(
                "voice chat is not connected or already playing", show_alert=True
            )
        else:
            callsmusic.pytgcalls.resume_stream(chet_id)
            await cb.message.edit(psn, reply_markup=keyboard)

    elif type_ == "puse":
        mps = "⏸ music playback has paused"
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "paused"
        ):
            await cb.answer(
                "voice chat is not connected or already paused", show_alert=True
            )
        else:
            callsmusic.pytgcalls.pause_stream(chet_id)
            await cb.message.edit(mps, reply_markup=keyboard)

    elif type_ == "cls":
        await cb.message.delete()

    elif type_ == "menu":
        stats = updated_stats(cb.message.chat, qeue)
        marr = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⏹", "leave"),
                    InlineKeyboardButton("⏸", "puse"),
                    InlineKeyboardButton("▶️", "resume"),
                    InlineKeyboardButton("⏭", "skip"),
                ],
                [
                    InlineKeyboardButton("📖 Playlist", "playlist"),
                ],
                [InlineKeyboardButton("🗑 Close", "cls")],
            ]
        )
        await cb.message.edit(stats, reply_markup=marr)

    elif type_ == "skip":
        nmq = "❌ no more music in __Queues__\n\n» **userbot leaving** voice chat"
        mmk = "⏭ __You've skipped to the next music__"
        if qeue:
            qeue.pop(0)
        if chet_id not in callsmusic.pytgcalls.active_calls:
            await cb.answer(
                "assistant is not connected to voice chat !", show_alert=True
            )
        else:
            callsmusic.queues.task_done(chet_id)

            if callsmusic.queues.is_empty(chet_id):
                callsmusic.pytgcalls.leave_group_call(chet_id)

                await cb.message.edit(
                    nmq,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🗑 Close", callback_data="closed")]]
                    ),
                )
            else:
                callsmusic.pytgcalls.change_stream(
                    chet_id, callsmusic.queues.get(chet_id)["file"]
                )
                await cb.message.edit(mmk, reply_markup=keyboard)

    elif type_ == "leave":
        kntls = "✅ __The Userbot has disconnected from voice chat__"
        if chet_id in callsmusic.pytgcalls.active_calls:
            try:
                callsmusic.queues.clear(chet_id)
            except QueueEmpty:
                pass

            callsmusic.pytgcalls.leave_group_call(chet_id)
            await cb.message.edit(
                    kntls,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🗑 Close", callback_data="closed")]]
                    ),
                )
        else:
            await cb.answer(
                "assistant is not connected to voice chat !", show_alert=True
            )


@Client.on_message(command(["play", f"play@{BOT_USERNAME}"]) & other_filters)
async def play(_, message: Message):
    global que
    global useer
    if message.chat.id in DISABLED_GROUPS:
        return
    lel = await message.reply("🔎 **Searching**")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id
    try:
        user = await USER.get_me()
    except:
        user.first_name = "helper"
    usar = user
    wew = usar.id 
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        f"<b>please add {user.first_name} to your channel.</b>",
                    )
                    pass
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>💡 **To use me, I need to be an Administrator with the permissions:\n\n» ❌ __Delete messages__\n» ❌ __Ban users__\n» ❌ __Add users__\n» ❌ __Manage voice chat__**\n\n**Then type /reload**</b>",
                    )
                    return
                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message.chat.id, "**__I'm joined to this group for playing music on voice chat__**"
                    )
                    await lel.edit(
                        "<b>💡 helper userbot joined your chat</b>",
                    )
                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>⛑ Flood Wait Error ⛑\nAssistant tidak dapat bergabung dengan grup Anda karena banyaknya permintaan bergabung untuk userbot! Pastikan pengguna tidak dibanned dalam grup."
                        f"\n\nAtau tambahkan @{ASSISTANT_NAME} secara manual ke Grup Anda dan coba lagi</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i>{user.first_name} was banned in this group, ask admin to unban @{ASSISTANT_NAME} manually.</i>"
        )
        return
    text_links=None
    if message.reply_to_message:
        if message.reply_to_message.audio:
            pass
        entities = []
        if message.entities:
            entities += entities
        elif message.caption_entities:
            entities += message.caption_entities
        if message.reply_to_message:
            text = message.reply_to_message.text \
                or message.reply_to_message.caption
            if message.reply_to_message.entities:
                entities = message.reply_to_message.entities + entities
        else:
            text = message.text or message.caption

        urls = [entity for entity in entities if entity.type == 'url']
        text_links = [
            entity for entity in entities if entity.type == 'text_link'
        ]
    else:
        urls=None
    if text_links:
        urls = True
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"❌ **music with duration more than** `{DURATION_LIMIT}` **minutes, can't play !**"
            )
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🎚️ Menu ", callback_data="menu"),
                    InlineKeyboardButton("🗑️ Close", callback_data="closed"),
                ]
            ]
        )
        file_name = get_file_name(audio)
        title = audio.file
        thumb_name = "https://telegra.ph/file/f6086f8909fbfeb0844f2.png"
        thumbnail = thumb_name
        ctitle = message.chat.title
        ctitle = await CHAT_TITLE(ctitle)
        duration = convert_seconds(audio.duration)
        views = "Locally added"
        requested_by = message.from_user.first_name
        await generate_cover(title, thumbnail, ctitle)
        file_path = await converter.convert(
            (await message.reply_to_message.download(file_name))
            if not path.isfile(path.join("downloads", file_name))
            else file_name
        )
    elif urls:
        query = toxt
        await lel.edit("🔎 **Searching**")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            url = f"https://youtube.com{results[0]['url_suffix']}"
            # print(results)
            title = results[0]["title"]
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f"{title}.jpg"
            ctitle = message.chat.title
            ctitle = await CHAT_TITLE(ctitle)
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, "wb").write(thumb.content)
            duration = results[0]["duration"]
            results[0]["url_suffix"]
            views = results[0]["views"]
        except Exception as e:
            await lel.delete()
            await lel.edit("❌ **couldn't find song**")
            print(str(e))
            return
        dlurl=url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
         [
            [
                InlineKeyboardButton("🎚️ Menu ", callback_data="menu"),
                InlineKeyboardButton("🗑️ Close", callback_data="closed"),
            ]
         ]
        )
        requested_by = message.from_user.first_name
        await generate_cover(title, thumbnail, ctitle)
        file_path = await converter.convert(youtube.download(url))        
    else:
        query = ""
        for i in message.command[1:]:
            query += " " + str(i)
        print(query)
        ydl_opts = {"format": "bestaudio[ext=m4a]"}

        try:
          results = YoutubeSearch(query, max_results=5).to_dict()
        except:
          await lel.edit("Give me something to play")
        # Looks like hell. Aren't it?? FUCK OFF
        try:
            toxxt = "\n"
            j = 0
            useer=user_name
            emojilist = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣"]
            while j < 5:
                toxxt += f"{emojilist[j]} [{results[j]['title'][:27]}...](https://youtube.com{results[j]['url_suffix']})\n"
                toxxt += f" ├ 💡 Duration - {results[j]['duration']}\n"
                toxxt += f" └ ⚡ __Powered by {BOT_NAME} AI__\n\n"
                j += 1            
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("1️⃣", callback_data=f'plll 0|{query}|{user_id}'),
                        InlineKeyboardButton("2️⃣", callback_data=f'plll 1|{query}|{user_id}'),
                        InlineKeyboardButton("3️⃣", callback_data=f'plll 2|{query}|{user_id}'),
                    ],
                    [
                        InlineKeyboardButton("4️⃣", callback_data=f'plll 3|{query}|{user_id}'),
                        InlineKeyboardButton("5️⃣", callback_data=f'plll 4|{query}|{user_id}')
                    ],
                    [InlineKeyboardButton(text="🗑 Close", callback_data="cls")],
                ]
            )
            await message.reply_photo(
                photo=f"{THUMB_IMG}", 
                caption=toxxt, 
                reply_markup=keyboard
            )
            await lel.delete()
            return

        except:

            try:
                url = f"https://youtube.com{results[0]['url_suffix']}"
                title = results[0]["title"]
                thumbnail = results[0]["thumbnails"][0]
                thumb_name = f"{title}.jpg"
                ctitle = message.chat.title
                ctitle = await CHAT_TITLE(ctitle)
                thumb = requests.get(thumbnail, allow_redirects=True)
                open(thumb_name, "wb").write(thumb.content)
                duration = results[0]["duration"]
                results[0]["url_suffix"]
                views = results[0]["views"]
            except Exception as e:
                await lel.delete()
                await _.send_photo(chid,
                photo=f"{THUMB_IMG}", 
                caption="😕 **Invalid Syntax try to read the help on button bellow!**",  
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                           InlineKeyboardButton("Group Support", url=f"https://t.me/{GROUP_SUPPORT}"),
                        ],
                        [
                           InlineKeyboardButton("See Command", callback_data="cbhplay"),
                        ],
                        [
                           InlineKeyboardButton("🗑️ Close", callback_data="closed"),
                        ],
                    ]
                )
                )
                print(str(e))
                return
            dlurl=url
            keyboard = InlineKeyboardMarkup(
                 [
            [
                InlineKeyboardButton("🎚️ Menu ", callback_data="menu"),
                InlineKeyboardButton("🗑️ Close", callback_data="closed"),
            ],
        ]
    )
            requested_by = message.from_user.first_name
            await generate_cover(title, thumbnail, ctitle)
            file_path = await converter.convert(youtube.download(url))   
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        url = message.reply_to_message.link
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await lel.delete()
        await _.send_photo(chid,
            photo="final.png",
            caption=f"🏷 **Name:** [{title}]({url})\n⏱ **Duration:** `{duration}`\n🎧 **Request by:** {message.from_user.mention}\n\n🔢 Track position » `{position}`",
            reply_markup=keyboard
        )
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        url = message.reply_to_message.link
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            message.reply("😕 **voice chat not found**\n\n» please turn on the voice chat first")
            return
        await lel.delete()
        await _.send_photo(chid,
            photo="final.png",
            caption = f"🏷 **Name:** [{title}]({url})\n⏱ **duration:** `{duration}`\n💡 **Status:** `Playing`\n" \
                    + f"🎧 **Request by:** {r_by.mention} \n",
            reply_markup=keyboard
        )
        os.remove("final.png")
        return
    text_links=None
    if message.reply_to_message:
        if message.reply_to_message.voice:
            pass
        entities = []
        if message.entities:
            entities += entities
        elif message.caption_entities:
            entities += message.caption_entities
        if message.reply_to_message:
            text = message.reply_to_message.text \
                or message.reply_to_message.caption
            if message.reply_to_message.entities:
                entities = message.reply_to_message.entities + entities
        else:
            text = message.text or message.caption

        urls = [entity for entity in entities if entity.type == 'url']
        text_links = [
            entity for entity in entities if entity.type == 'text_link'
        ]
    else:
        urls=None
    if text_links:
        urls = True
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"❌ **music with duration more than** `{DURATION_LIMIT}` **minutes, can't play !**"
            )
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🎚️ Menu ", callback_data="menu"),
                    InlineKeyboardButton("🗑️ Close", callback_data="closed"),
                ]
            ]
        )
        file_name = get_file_name(audio)
        title = file_name
        thumb_name = "https://telegra.ph/file/f6086f8909fbfeb0844f2.png"
        thumbnail = thumb_name
        ctitle = message.chat.title
        ctitle = await CHAT_TITLE(ctitle)
        duration = convert_seconds(audio.duration)
        views = "Locally added"
        requested_by = message.from_user.first_name
        await generate_cover(title, thumbnail, ctitle)
        file_path = await converter.convert(
            (await message.reply_to_message.download(file_name))
            if not path.isfile(path.join("downloads", file_name))
            else file_name
        )
    elif urls:
        query = toxt
        await lel.edit("🔎 **Searching**")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            url = f"https://youtube.com{results[0]['url_suffix']}"
            # print(results)
            title = results[0]["title"]
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f"{title}.jpg"
            ctitle = message.chat.title
            ctitle = await CHAT_TITLE(ctitle)
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, "wb").write(thumb.content)
            duration = results[0]["duration"]
            results[0]["url_suffix"]
            views = results[0]["views"]
        except Exception as e:
            await lel.delete()
            await lel.edit("❌ **couldn't find song**")
            print(str(e))
            return
        dlurl=url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
         [
            [
                InlineKeyboardButton("🎚️ Menu ", callback_data="menu"),
                InlineKeyboardButton("🗑️ Close", callback_data="closed"),
            ]
         ]
        )
        requested_by = message.from_user.first_name
        await generate_cover(title, thumbnail, ctitle)
        file_path = await converter.convert(youtube.download(url))
        chat_id = get_chat_id(message.chat)
        if chat_id in callsmusic.pytgcalls.active_calls:
            position = await queues.put(chat_id, file=file_path)
            qeue = que.get(chat_id)
            s_name = title
            url = message.reply_to_message.link
            r_by = message.from_user
            loc = file_path
            appendable = [s_name, r_by, loc]
            qeue.append(appendable)
            await lel.delete()
            await _.send_photo(chid,
                photo="final.png",
                caption=f"🏷 **Name:** [Telegram audio file]({url})\n⏱ **Duration:** `{duration}`\n🎧 **Request by:** {message.from_user.mention}\n\n🔢 Track position » `{position}`",
                reply_markup=keyboard
            )
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        url = message.reply_to_message.link
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            message.reply("😕 **voice chat not found**\n\n» please turn on the voice chat first")
            return
        await lel.delete()
        await _.send_photo(chid,
            photo="final.png",
            caption = f"🏷 **Name:** [Telegram audio file]({url})\n⏱ **duration:** `{duration}`\n💡 **Status:** `Playing`\n" \
                    + f"🎧 **Request by:** {r_by.mention} \n",
            reply_markup=keyboard
        )
        os.remove("final.png")


@Client.on_callback_query(filters.regex(pattern=r"plll"))
async def lol_cb(b, cb):
    global que
    cbd = cb.data.strip()
    chat_id = cb.message.chat.id
    typed_=cbd.split(None, 1)[1]
    try:
        x,query,useer_id = typed_.split("|")      
    except:
        await cb.message.edit("❌ **couldn't find song**, please provide the correct song name.")
        return
    useer_id = int(useer_id)
    if cb.from_user.id != useer_id:
        await cb.answer("💡 this is not for you !", show_alert=True)
        return
    await cb.message.delete()
    x=int(x)
    try:
        useer_name = cb.message.reply_to_message.from_user.first_name
    except:
        useer_name = cb.message.from_user.first_name
    results = YoutubeSearch(query, max_results=5).to_dict()
    resultss=results[x]["url_suffix"]
    title=results[x]["title"]
    thumbnail=results[x]["thumbnails"][0]
    duration=results[x]["duration"]
    views=results[x]["views"]
    url = f"https://www.youtube.com{resultss}"
    try:    
        secmul, dur, dur_arr = 1, 0, duration.split(":")
        for i in range(len(dur_arr)-1, -1, -1):
            dur += (int(dur_arr[i]) * secmul)
            secmul *= 60
        if (dur / 60) > DURATION_LIMIT:
             await b.send_message(chat_id, f"❌ **music with duration more than** `{DURATION_LIMIT}` **minutes, can't play !**")
             return
    except:
        pass
    try:
        thumb_name = f"{title}.jpg"
        ctitle = cb.message.chat.title
        ctitle = await CHAT_TITLE(ctitle)
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
    except Exception as e:
        print(e)
        return
    dlurl=url
    dlurl=dlurl.replace("youtube", "youtubepp")
    keyboard = InlineKeyboardMarkup(
     [
        [
            InlineKeyboardButton("🎚️ Menu ", callback_data="menu"),
            InlineKeyboardButton("🗑️ Close", callback_data="closed"),
        ]
     ]
    )
    requested_by = useer_name
    await generate_cover(title, thumbnail, ctitle)
    file_path = await converter.convert(youtube.download(url))  
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await b.send_photo(
        chat_id,
        photo="final.png",
        caption=f"🏷 **Name:** [{title}]({url})\n⏱ **Duration:** `{duration}`\n🎧 **Request by:** {r_by.mention}\n\n🔢 Track position » `{position}`",
        reply_markup=keyboard,
        )
        if path.exists("final.png"):
            os.remove("final.png")
    else:
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        await b.send_photo(
        chat_id,
        photo="final.png",
        caption = f"🏷 **Name:** [{title}]({url})\n⏱ **duration:** `{duration}`\n💡 **Status:** `Playing`\n" \
                + f"🎧 **Request by:** {r_by.mention} \n",
        reply_markup=keyboard,
        )
        if path.exists("final.png"):
            os.remove("final.png")


@Client.on_message(command(["ytp", f"ytp@{BOT_USERNAME}"]) & filters.group & ~filters.edited)
async def ytplay(_, message: Message):
    global que
    if message.chat.id in DISABLED_GROUPS:
        return
    lel = await message.reply("🔎 **Searching**")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "helper"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        f"<b>please add {user.first_name} to your channel first</b>",
                    )
                    pass
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>💡 **To use me, I need to be an Administrator with the permissions:\n\n» ❌ __Delete messages__\n» ❌ __Ban users__\n» ❌ __Add users__\n» ❌ __Manage voice chat__\n\n**Then type /reload**</b>",
                    )
                    return
                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message.chat.id, "**__I'm joined your group for playing music__**"
                    )
                    await lel.edit(
                        "<b>💡 Helper userbot joined!\n\n• Jika terjadi masalah, laporkan ke @kenbotsupport</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>Flood Wait Error\n{user.first_name} tidak dapat bergabung dengan grup Anda karena banyaknya permintaan bergabung untuk userbot! Pastikan pengguna tidak dibanned dalam grup."
                        f"\n\nAtau tambahkan @{ASSISTANT_NAME} secara manual ke Grup Anda dan coba lagi</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i>{user.first_name} was banned in this group, ask admin to unban @{ASSISTANT_NAME} manually.</i>"
        )
        return
    user_id = message.from_user.id
    user_name = message.from_user.first_name
     

    query = ""
    for i in message.command[1:]:
        query += " " + str(i)
    print(query)
    ydl_opts = {"format": "bestaudio[ext=m4a]"}
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        url = f"https://youtube.com{results[0]['url_suffix']}"
        # print(results)
        title = results[0]["title"]
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"thumb{title}.jpg"
        ctitle = message.chat.title
        ctitle = await CHAT_TITLE(ctitle)
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
        duration = results[0]["duration"]
        results[0]["url_suffix"]
        views = results[0]["views"]

    except Exception as e:
        await lel.delete()
        await _.send_photo(chid,
        photo=f"{THUMB_IMG}", 
        caption="😕 **Invalid Syntax try to read the help on button below!**", 
        reply_markup=InlineKeyboardMarkup(
            [
                [
                   InlineKeyboardButton("Group Support", url=f"https://t.me/{GROUP_SUPPORT}"),
                ],
                [
                   InlineKeyboardButton("See Command", callback_data="cbhplay"),
                ],
                [
                   InlineKeyboardButton("🗑️ Close", callback_data="closed"),
                ],
            ]
        )
        )
        print(str(e))
        return
    dlurl=url
    dlurl=dlurl.replace("youtube","youtubepp")
    keyboard = InlineKeyboardMarkup(
     [
        [
            InlineKeyboardButton("🎚️ Menu", callback_data="menu"),
            InlineKeyboardButton("🗑️ Close", callback_data="closed"),
        ]
     ]
    )
    requested_by = message.from_user.first_name
    await generate_cover(title, thumbnail, ctitle)
    file_path = await converter.convert(youtube.download(url))
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await lel.delete()
        await _.send_photo(
            chid,
            photo="final.png",
            caption=f"🏷 **Name:** [{title}]({url})\n⏱ **Duration:** `{duration}`\n🎧 **Request by:** {r_by.mention}\n\n🔢 Track position » `{position}`",
                   reply_markup=keyboard,
        )
        os.remove("final.png")
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            message.reply("** sorry, no active voice chat here, please turn on the voice chat first**")
            return
        await lel.delete()
        await _.send_photo(
            chid,
            photo="final.png",
            caption = f"🏷 **Name:** [{title}]({url})\n⏱ **duration:** `{duration}`\n💡 **Status:** `Playing`\n" \
                    + f"🎧 **Request by:** {r_by.mention} \n",
                    reply_markup=keyboard)
        os.remove("final.png")
