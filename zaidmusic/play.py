import os
from os import path
from typing import Callable
from asyncio.queues import QueueEmpty

import aiofiles
import aiohttp
import converter
import ffmpeg
import requests
from cache.admins import admins as a
from callsmusic import callsmusic
from callsmusic.callsmusic import client as USER
from callsmusic.queues import queues
from config import (
    ASSISTANT_NAME,
    BOT_NAME,
    BOT_USERNAME,
    DURATION_LIMIT,
    GROUP_SUPPORT,
    THUMB_IMG,
    CMD_IMG,
    UPDATES_CHANNEL,
    que,
)
from downloaders import youtube
from helpers.admins import get_administrators
from helpers.channelmusic import get_chat_id
from helpers.chattitle import CHAT_TITLE
from helpers.decorators import authorized_users_only
from helpers.filters import command, other_filters
from helpers.gets import get_url, get_file_name
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant
from pytgcalls import StreamType
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.types.input_stream import InputStream
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtube_search import YoutubeSearch

# plus

chat_id = None
DISABLED_GROUPS = []
useer = "NaN"



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

def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)

def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))

def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage

async def generate_cover(title, thumbnail, ctitle):
    async with aiohttp.ClientSession() as session, session.get(thumbnail) as resp:
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
    font = ImageFont.truetype("etc/regular.ttf", 52)
    font2 = ImageFont.truetype("etc/medium.ttf", 76)
    draw.text((27, 538), f"Playing on {ctitle[:8]}..", (0, 0, 0), font=font)
    draw.text((27, 612), f"{title[:18]}...", (0, 0, 0), font=font2)
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")


@Client.on_message(
    command(["playlist", f"playlist@{BOT_USERNAME}"]) & filters.group & ~filters.edited
)
async def playlist(client, message):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Gʀᴏᴜᴘ", url=f"https://t.me/{GROUP_SUPPORT}"),
                InlineKeyboardButton(
                    "Cʜᴀɴɴᴇʟ", url=f"https://t.me/SUPERIOR_Bots"
                ),
            ]
        ]
    )

    global que
    if message.chat.id in DISABLED_GROUPS:
        return
    queue = que.get(message.chat.id)
    if not queue:
        await message.reply_text("❌ **no music is currently playing**")
    temp = []
    for t in queue:
        temp.append(t)
    now_playing = temp[0][0]
    by = temp[0][1].mention(style="md")
    msg = "☑️ **ɴᴏᴡ ᴘʟᴀʏɪɴɢ** on {}".format(message.chat.title)
    msg += "\n\n• " + now_playing
    msg += "\n• Req By " + by
    temp.pop(0)
    if temp:
        msg += "\n\n"
        msg += "🔖 **Queued Song:**"
        for song in temp:
            name = song[0]
            usr = song[1].mention(style="md")
            msg += f"\n\n• {name}"
            msg += f"\n• Req by {usr}"
    await message.reply_text(msg, reply_markup=keyboard)

# ============================= Settings =========================================

def updated_stats(chat, queue, vol=100):
    if chat.id in callsmusic.pytgcalls.active_calls:
        stats = "⚙ settings for **{}**".format(chat.title)
        if len(que) > 0:
            stats += "\n\n"
            stats += "• volume: `{}%`\n".format(vol)
            stats += "• song played: `{}`\n".format(len(que))
            stats += "• now playing: **{}**\n".format(queue[0][0])
            stats += "• request by: {}".format(queue[0][1].mention(style="md"))
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
                InlineKeyboardButton("⏭", "skip"),
            ],
            [
                InlineKeyboardButton("Playlist", "playlist"),
            ],
            [InlineKeyboardButton("🗑", "cls")],
        ]
    )
    return mar


@Client.on_message(
    command(["player", f"player@{BOT_USERNAME}"]) & filters.group & ~filters.edited
)
@authorized_users_only
async def settings(client, message):
    global que
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
        await message.reply(
            "😕 **ɪɴᴀᴄᴛɪᴠᴇ ᴠᴄ ᴄʜᴀᴛ ᴘʟᴢ ꜱᴛᴀʀᴛ ᴠᴄ ᴄʜᴀᴛ ꜰɪʀꜱᴛ**"
        )


@Client.on_message(
    command(["music", f"music@{BOT_USERNAME}"])
    & ~filters.edited
    & ~filters.bot
    & ~filters.private
)
@authorized_users_only
async def music_onoff(_, message):
    global DISABLED_GROUPS
    try:
        message.from_user.id
    except:
        return
    if len(message.command) != 2:
        await message.reply_text(
            "**• usage:**\n\n `/music on` & `/music off`"
        )
        return
    status = message.text.split(None, 1)[1]
    message.chat.id
    if status in ("ON", "on", "On"):
        lel = await message.reply("`processing...`")
        if not message.chat.id in DISABLED_GROUPS:
            await lel.edit("» **music player already turned on.**")
            return
        DISABLED_GROUPS.remove(message.chat.id)
        await lel.edit(f"✅ **music player turned on**\n\n💬 `{message.chat.id}`")

    elif status in ("OFF", "off", "Off"):
        lel = await message.reply("`processing...`")

        if message.chat.id in DISABLED_GROUPS:
            await lel.edit("» **music player already turned off.**")
            return
        DISABLED_GROUPS.append(message.chat.id)
        await lel.edit(f"✅ **music player turned off**\n\n💬 `{message.chat.id}`")
    else:
        await message.reply_text(
            "**• usage:**\n\n `/music on` & `/music off`"
        )


@Client.on_callback_query(filters.regex(pattern=r"^(playlist)$"))
async def p_cb(b, cb):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Gʀᴏᴜᴘ", url=f"https://t.me/{GROUP_SUPPORT}"),
                InlineKeyboardButton(
                    "Cʜᴀɴɴᴇʟ", url=f"https://t.me/{UPDATES_CHANNEL}"
                ),
            ],
            [InlineKeyboardButton("🔙", callback_data="menu")],
        ]
    )

    global que
    que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    cb.message.chat
    cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("❌ **no music is currently playing**")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "💡 **now playing** on {}".format(cb.message.chat.title)
        msg += "\n\n• " + now_playing
        msg += "\n• Req by " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "🔖 **Queued Song:**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n\n• {name}"
                msg += f"\n• Req by {usr}"
        await cb.message.edit(msg, reply_markup=keyboard)


@Client.on_callback_query(
    filters.regex(pattern=r"^(play|pause|skip|leave|puse|resume|menu|cls)$")
)
@cb_admin_check
async def m_cb(b, cb):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Gʀᴏᴜᴘ", url=f"https://t.me/{GROUP_SUPPORT}"),
                InlineKeyboardButton(
                    "Cʜᴀɴɴᴇʟ", url=f"https://t.me/{UPDATES_CHANNEL}"
                ),
            ],
            [InlineKeyboardButton("Back", callback_data="menu")],
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

    cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "pause":
        ACTV_CALLS = []
        for x in callsmusic.pytgcalls.active_calls:
            ACTV_CALLS.append(int(x.chet_id))
        if int(chet_id) not in ACTV_CALLS:
            await cb.answer(
                "userbot is not connected to voice chat.", show_alert=True
            )
        else:
            await callsmusic.pytgcalls.pause_stream(chet_id)
            
            await cb.answer("music paused")
            await cb.message.edit(
                updated_stats(m_chat, qeue), reply_markup=r_ply("play")
            )

    elif type_ == "play":
        ACTV_CALLS = []
        for x in callsmusic.pytgcalls.active_calls:
            ACTV_CALLS.append(int(x.chet_id))
        if int(chet_id) not in ACTV_CALLS:
            await cb.answer(
                "userbot is not connected to voice chat.", show_alert=True
            )
        else:
            await callsmusic.pytgcalls.resume_stream(chet_id)
            
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
        msg = "☑️ **ɴᴏᴡ ᴘʟᴀʏɪɴɢ** on {}".format(cb.message.chat.title)
        msg += "\n• " + now_playing
        msg += "\n• Req by " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "🔖 **Queued Song:**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n\n• {name}"
                msg += f"\n• Req by {usr}"
        await cb.message.edit(msg, reply_markup=keyboard)

    elif type_ == "resume":
        psn = "▶ music playback has resumed"
        ACTV_CALLS = []
        for x in callsmusic.pytgcalls.active_calls:
            ACTV_CALLS.append(int(x.chet_id))
        if int(chet_id) not in ACTV_CALLS:
            await cb.answer(
                "voice chat is not connected or already playing", show_alert=True
            )
        else:
            await callsmusic.pytgcalls.resume_stream(chet_id)
            await cb.message.edit(psn, reply_markup=keyboard)

    elif type_ == "puse":
        spn = "⏸ music playback has paused"
        ACTV_CALLS = []
        for x in callsmusic.pytgcalls.active_calls:
            ACTV_CALLS.append(int(x.chet_id))
        if int(chet_id) not in ACTV_CALLS:
            await cb.answer(
                "voice chat is not connected or already paused", show_alert=True
            )
        else:
            await callsmusic.pytgcalls.pause_stream(chet_id)
            await cb.message.edit(spn, reply_markup=keyboard)

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
                    InlineKeyboardButton("Playlist", "playlist"),
                ],
                [InlineKeyboardButton("🗑", "cls")],
            ]
        )
        await cb.message.edit(stats, reply_markup=marr)

    elif type_ == "skip":
        nmq = "❌ no more __Queues__\n\n» **userbot leaving** voice chat"
        mmk = "⏭ skipped"
        if qeue:
            qeue.pop(0)
        ACTV_CALLS = []
        for x in callsmusic.pytgcalls.active_calls:
            ACTV_CALLS.append(int(x.chet_id))
        if int(chet_id) not in ACTV_CALLS:
            await cb.answer(
                "assistant is not connected to voice chat !", show_alert=True
            )
        else:
            callsmusic.queues.task_done(chet_id)
            
            if callsmusic.queues.is_empty(chet_id):
                await callsmusic.pytgcalls.leave_group_call(chet_id)
                
                await cb.message.edit(
                    nmq,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🗑", callback_data="close")]]
                    ),
                )
            else:
                await callsmusic.pytgcalls.change_stream(
                    chet_id, 
                    InputStream(
                        InputAudioStream(
                            callsmusic.queues.get(chet_id)["file"],
                        ),
                    ),
                )
                await cb.message.edit(mmk, reply_markup=keyboard)

    elif type_ == "leave":
        hps = "✅ **the music playback has ended**"
        ACTV_CALLS = []
        for x in callsmusic.pytgcalls.active_calls:
            ACTV_CALLS.append(int(x.chet_id))
        if int(chet_id) not in ACTV_CALLS:
            try:
                callsmusic.queues.clear(chet_id)
            except QueueEmpty:
                pass
            await callsmusic.pytgcalls.leave_group_call(chet_id)
            await cb.message.edit(
                hps,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🗑 Close", callback_data="close")]]
                ),
            )
        else:
            await cb.answer(
                "userbot is not connected to voice chat.", show_alert=True
            )



@Client.on_message(command(["play", f"ytplay"]) & other_filters)
async def ytplay(_, message: Message):
    
    bttn = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇꜱ", url=f"https://t.me/{UPDATES_CHANNEL}")
            ],[
                InlineKeyboardButton("🗑", callback_data="close")
            ]
        ]
    )
    
    nofound = "😕 **ɪ ᴅɪᴅɴ'ᴛ ᴀʙʟᴇ ᴛᴏ ꜰɪɴᴅ ᴜʀ ꜱᴏɴɢ ᴘʟᴢ ᴍᴀᴋᴇ ᴄᴜʀʀᴇᴄᴛ ꜱᴘᴇʟʟ ᴛʜᴇʀᴇ**"
    
    global que
    if message.chat.id in DISABLED_GROUPS:
        return
    lel = await message.reply("🔎")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "music assistant"
    usar = user
    wew = usar.id
    try:
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        f"💝 **ᴘʟᴢ ᴀᴅᴅ ᴍᴜꜱɪᴄ ʜᴇʟᴘᴇʀ ᴛᴏ ᴜʀ ᴄʜᴀɴɴᴇʟ**",
                    )
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "☑️ **ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴꜱᴛʀᴀᴛɪᴏɴ ꜰɪʀꜱᴛ ᴛᴏ ᴜꜱᴇ ᴍᴇ**",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await lel.edit(
                        f"✅ **userbot succesfully entered chat**",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"🔴 **ꜰʟᴏᴏᴅ ᴡᴀɪᴛ ᴇʀʀᴏʀ** 🔴 \n\n**ʜᴇʟᴘᴇʀ ᴜꜱᴇʀʙᴏᴛ ᴜɴᴀʙʟᴇ ᴛᴏ ᴊᴏɪɴ ᴜʀ ᴄʜᴀᴛ @{ASSISTANT_NAME} ᴘʟᴢ ᴀᴅᴅ ᴍᴀɴᴜᴀʟʟʏ .**"
                        f"\n\n**ᴏʀ ᴄᴏɴᴛᴀᴄᴛ @{GROUP_SUPPORT}.**",
                    )
    try:
        await USER.get_chat(chid)
    except:
        await lel.edit(
            f"»**unban @{ASSISTANT_NAME} and add to this group again manually, or type /reload if u Face any error then Report this errors in @{GROUP_SUPPORT}.**"
        )
        return

    query = ""
    for i in message.command[1:]:
        query += " " + str(i)
    print(query)
    await lel.edit("🔄")
    ydl_opts = {"format": "bestaudio/best"}
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        url = f"https://youtube.com{results[0]['url_suffix']}"
        title = results[0]["title"][:70]
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"{title}.jpg"
        ctitle = message.chat.title
        ctitle = await CHAT_TITLE(ctitle)
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
        duration = results[0]["duration"]
        results[0]["url_suffix"]

    except Exception as e:
        await lel.delete()
        await message.reply_photo(
            photo=f"{CMD_IMG}",
            caption=nofound,
            reply_markup=bttn,
        )
        print(str(e))
        return
    try:
        secmul, dur, dur_arr = 1, 0, duration.split(":")
        for i in range(len(dur_arr) - 1, -1, -1):
            dur += int(dur_arr[i]) * secmul
            secmul *= 60
        if (dur / 60) > DURATION_LIMIT:
            await lel.edit(
                f"❌ **ᴍᴜꜱɪᴄ ɴᴏ ʟᴏɴɢᴇʀ ᴛʜᴀɴ** `{DURATION_LIMIT} !**"
            )
            return
    except:
        pass
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("ᴍᴇɴᴜ", callback_data="menu"),
                InlineKeyboardButton("🗑️", callback_data="cls"),
            ],
            [InlineKeyboardButton("Cʜᴀɴɴᴇʟ", url=f"https://t.me/{UPDATES_CHANNEL}")],
        ]
    )
    await generate_cover(title, thumbnail, ctitle)
    file_path = await converter.convert(youtube.download(url))
    ACTV_CALLS = []
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS.append(int(x.chat_id))
    if int(message.chat.id) in ACTV_CALLS:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await lel.delete()
        await message.reply_photo(
            photo="final.png",
            caption=f"💝 **Qᴜᴇᴜᴇ »** `{position}`\n\n🏷 **ɴᴀᴍᴇ:** [{title[:35]}...]({url})\n⏱ **ᴅᴜʀᴀᴛɪᴏɴ:** `{duration}`\n🎧 **ᴢᴀɪᴅ ᴜꜱᴇʀ ʙʏ:** {message.from_user.mention}",
            reply_markup=keyboard,
        )
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
            await callsmusic.pytgcalls.join_group_call(
                chat_id, 
                InputStream(
                    InputAudioStream(
                        file_path,
                    ),
                ),
                stream_type=StreamType().local_stream,
            )
        except:
            await lel.edit(
                "😕 **ɪɴᴀᴄᴛɪᴠᴇ ᴠᴄ ᴄʜᴀᴛ ᴘʟᴢ ꜱᴛᴀʀᴛ ᴠᴄ ᴄʜᴀᴛ ꜰɪʀꜱᴛ**"
            )
            return
        await lel.delete()
        await message.reply_photo(
            photo="final.png",
            caption=f"☑️ **ɴᴀᴍᴇ:** [{title[:70]}]({url})\n⏱ **ᴅᴜʀᴀᴛɪᴏɴ:** `{duration}`\n"
            + f"🎧 **ᴢᴀɪᴅ ᴜꜱᴇʀ ʙʏ:** {message.from_user.mention}",
            reply_markup=keyboard,
        )
        os.remove("final.png")
