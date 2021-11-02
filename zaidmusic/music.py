# Copyright (C) 2021 By Veez Music-Project
# Commit Start Date 20/10/2021
# Finished On 28/10/2021

import asyncio
import re

from config import BOT_USERNAME, GROUP_SUPPORT, IMG_1, IMG_2, UPDATES_CHANNEL
from driver.filters import command, other_filters
from driver.queues import QUEUE, add_to_queue
from driver.veez import call_py
from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pytgcalls import StreamType
from pytgcalls.types.input_stream import AudioPiped
from youtubesearchpython import VideosSearch


def ytsearch(query):
    try:
        search = VideosSearch(query, limit=1)
        for r in search.result()["result"]:
            ytid = r["id"]
            if len(r["title"]) > 34:
                songname = r["title"][:70]
            else:
                songname = r["title"]
            url = f"https://www.youtube.com/watch?v={ytid}"
        return [songname, url]
    except Exception as e:
        print(e)
        return 0


async def ytdl(link):
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "-g",
        "-f",
        "bestaudio",
        f"{link}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().split("\n")[0]
    else:
        return 0, stderr.decode()


@Client.on_message(command(["play", f"play@{BOT_USERNAME}"]) & other_filters)
async def play(_, m: Message):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="• ꜱᴜᴘᴘᴏʀᴛ", url="t.me/superior_support"
                ),
                InlineKeyboardButton(
                    text="• ᴜᴘᴅᴀᴛᴇꜱ", url="t.me/superior_bots"
                ),
            ]
        ]
    )

    replied = m.reply_to_message
    chat_id = m.chat.id
    if replied:
        if replied.audio or replied.voice:
            suhu = await replied.reply("📥 **downloading audio...**")
            dl = await replied.download()
            link = replied.link
            if replied.audio:
                if replied.audio.title:
                    songname = replied.audio.title[:70]
                else:
                    if replied.audio.file_name:
                        songname = replied.audio.file_name[:70]
                    else:
                        songname = "Audio"
            elif replied.voice:
                songname = "Voice Note"
            if chat_id in QUEUE:
                pos = add_to_queue(chat_id, songname, dl, link, "Audio", 0)
                await suhu.delete()
                await m.reply_photo(
                    photo=f"{IMG_1}",
                    caption=f"💝 **ᴛʀᴀᴄᴋ ɪꜱ ᴀᴅᴅᴇᴅ ɪɴ Qᴜᴇᴜᴇ:** [{songname}]({url})\n💭 **ᴄʜᴀᴛ:** `{chat_id}`\n🎧 **ᴢᴀɪᴅ ᴜꜱᴇʀ ʙʏ:** {m.from_user.mention()}\n🔢 **ᴘᴏꜱɪᴛɪᴏɴ »** `{pos}`",
                    reply_markup=keyboard,
                )
            else:
                await call_py.join_group_call(
                    chat_id,
                    AudioPiped(
                        dl,
                    ),
                    stream_type=StreamType().pulse_stream,
                )
                add_to_queue(chat_id, songname, dl, link, "Audio", 0)
                await suhu.delete()
                await m.reply_photo(
                    photo=f"{IMG_2}",
                    caption=f"☑️ **ꜱᴛᴀʀᴛᴇᴅ ᴘʟᴀʏɪɴɢ:** [{songname}]({url})\n💭 **ᴄʜᴀᴛ:** `{chat_id}`\n💡 **ꜱᴛᴀᴛᴜꜱ:** `Playing`\n🎧 **ᴢᴀɪᴅ ᴜꜱᴇʀ ʙʏ:** {m.from_user.mention()}",
                    reply_markup=keyboard,
                )
        else:
            if len(m.command) < 2:
                await m.reply(
                    "» ᴛʏᴘᴇ ꜱᴏᴍᴇᴛʜɪɴɢ ᴛᴏ ᴘʟᴀʏ? 🤨**"
                )
            else:
                suhu = await m.reply("🔎")
                query = m.text.split(None, 1)[1]
                search = ytsearch(query)
                if search == 0:
                    await suhu.edit("❌ **ꜱᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ.**")
                else:
                    songname = search[0]
                    url = search[1]
                    veez, ytlink = await ytdl(url)
                    if veez == 0:
                        await suhu.edit(f"❌ ꜱᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ\n\n» `{ytlink}`")
                    else:
                        if chat_id in QUEUE:
                            pos = add_to_queue(
                                chat_id, songname, ytlink, url, "Audio", 0
                            )
                            await suhu.delete()
                            await m.reply_photo(
                                photo=f"{IMG_1}",
                                caption=f"💝 **ᴛʀᴀᴄᴋ ɪꜱ ᴀᴅᴅᴇᴅ ɪɴ Qᴜᴇᴜᴇ:** [{songname}]({url})\n💭 **ᴄʜᴀᴛ:** `{chat_id}`\n🎧 **ᴢᴀɪᴅ ᴜꜱᴇʀ ʙʏ:** {m.from_user.mention()}\n🔢 **ᴘᴏꜱɪᴛɪᴏɴ »** `{pos}`",
                                reply_markup=keyboard,
                            )
                        else:
                            try:
                                await call_py.join_group_call(
                                    chat_id,
                                    AudioPiped(
                                        ytlink,
                                    ),
                                    stream_type=StreamType().pulse_stream,
                                )
                                add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                                await suhu.delete()
                                await m.reply_photo(
                                    photo=f"{IMG_2}",
                                    caption=f"☑️ **ꜱᴛᴀʀᴛᴇᴅ ᴘʟᴀʏɪɴɢ:** [{songname}]({url})\n💭 **ᴄʜᴀᴛ:** `{chat_id}`\n💡 **ꜱᴛᴀᴛᴜꜱ:** `Playing`\n🎧 **ᴢᴀɪᴅ ᴜꜱᴇʀ ʙʏ:** {m.from_user.mention()}",
                                    reply_markup=keyboard,
                                )
                            except Exception as ep:
                                await m.reply_text(f"🚫 error: `{ep}`")

    else:
        if len(m.command) < 2:
            await m.reply(
                "» ᴛʏᴘᴇ ꜱᴏᴍᴇᴛʜɪɴɢ ᴛᴏ ᴘʟᴀʏ? 🤨**"
            )
        else:
            suhu = await m.reply("🔎")
            query = m.text.split(None, 1)[1]
            search = ytsearch(query)
            if search == 0:
                await suhu.edit("❌ **ꜱᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ.**")
            else:
                songname = search[0]
                url = search[1]
                veez, ytlink = await ytdl(url)
                if veez == 0:
                    await suhu.edit(f"❌ ꜱᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ\n\n» `{ytlink}`")
                else:
                    if chat_id in QUEUE:
                        pos = add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                        await suhu.delete()
                        await m.reply_photo(
                            photo=f"{IMG_1}",
                            caption=f"💝 **ᴛʀᴀᴄᴋ ɪꜱ ᴀᴅᴅᴇᴅ ɪɴ Qᴜᴇᴜᴇ:** [{songname}]({url})\n💭 **ᴄʜᴀᴛ:** `{chat_id}`\n🎧 **ᴢᴀɪᴅ ᴜꜱᴇʀ ʙʏ:** {m.from_user.mention()}\n🔢 **ᴘᴏꜱɪᴛɪᴏɴ »** `{pos}`",
                            reply_markup=keyboard,
                        )
                    else:
                        try:
                            await call_py.join_group_call(
                                chat_id,
                                AudioPiped(
                                    ytlink,
                                ),
                                stream_type=StreamType().pulse_stream,
                            )
                            add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                            await suhu.delete()
                            await m.reply_photo(
                                photo=f"{IMG_2}",
                                caption=f"☑️ **ꜱᴛᴀʀᴛᴇᴅ ᴘʟᴀʏɪɴɢ:** [{songname}]({url})\n💭 **ᴄʜᴀᴛ:** `{chat_id}`\n💡 **ꜱᴛᴀᴛᴜꜱ:** `Playing`\n🎧 **ᴢᴀɪᴅ ᴜꜱᴇʀ ʙʏ:** {m.from_user.mention()}",
                                reply_markup=keyboard,
                            )
                        except Exception as ep:
                            await m.reply_text(f"🚫 error: `{ep}`")


# stream is used for live streaming only

