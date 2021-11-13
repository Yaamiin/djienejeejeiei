from callsmusic import callsmusic
from callsmusic.queues import queues
from config import BOT_USERNAME, que
from cache.admins import admins
from helpers.channelmusic import get_chat_id
from helpers.dbtools import delcmd_is_on, delcmd_off, delcmd_on, handle_user_status
from helpers.decorators import authorized_users_only, errors
from helpers.filters import command, other_filters
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.types.input_stream import InputStream
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)


@Client.on_message()
async def _(bot: Client, cmd: Message):
    await handle_user_status(bot, cmd)


# Back Button
BACK_BUTTON = InlineKeyboardMarkup(
    [[InlineKeyboardButton("🔙 Go Back", callback_data="cbback")]]
)

# @Client.on_message(filters.text & ~filters.private)
# async def delcmd(_, message: Message):
#    if await delcmd_is_on(message.chat.id) and message.text.startswith("/") or message.text.startswith("!") or message.text.startswith("."):
#        await message.delete()
#    await message.continue_propagation()

# remove the ( # ) if you want the auto del cmd feature is on


@Client.on_message(command(["reload", f"adminchache"]) & other_filters)
async def update_admin(client, message):
    global admins
    new_admins = []
    new_ads = await client.get_chat_members(message.chat.id, filter="administrators")
    for u in new_ads:
        new_admins.append(u.user.id)
    admins[message.chat.id] = new_admins
    await message.reply_text(
        "✅ ᴀᴅᴍɪɴꜱ ᴜᴘᴅᴀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ**"
    )


# Control Menu Of Player
@Client.on_message(command(["control", f"panel"]) & other_filters)
@errors
@authorized_users_only
async def controlset(_, message: Message):
    await message.reply_text(
        "💡 **here is the control menu of bot :**",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⏸ pause", callback_data="cbpause"),
                    InlineKeyboardButton("▶️ resume", callback_data="cbresume"),
                ],
                [
                    InlineKeyboardButton("⏩ skip", callback_data="cbskip"),
                    InlineKeyboardButton("⏹ stop", callback_data="cbend"),
                ],
                [InlineKeyboardButton("⛔ anti cmd", callback_data="cbdelcmds")],
                [InlineKeyboardButton("🗑 Close", callback_data="close")],
            ]
        ),
    )


@Client.on_message(command(["pause", f"pause@{BOT_USERNAME}"]) & other_filters)
@errors
@authorized_users_only
async def pause(_, message: Message):
    chat_id = get_chat_id(message.chat)
    ACTV_CALL = []
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALL.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALL:
        await message.reply_text("❌ **ɴᴏᴛʜɪɴɢ**")
    else:
        await callsmusic.pytgcalls.pause_stream(chat_id)
        await message.reply_text(
            "⏸ **» ᴘᴀᴜꜱᴇᴅ.**"
        )


@Client.on_message(command(["resume", f"resume@{BOT_USERNAME}"]) & other_filters)
@errors
@authorized_users_only
async def resume(_, message: Message):
    chat_id = get_chat_id(message.chat)
    ACTV_CALL = []
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALL.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALL:
        await message.reply_text("❌ **ɴᴏᴛʜɪɴɢ**")
    else:
        await callsmusic.pytgcalls.resume_stream(chat_id)
        await message.reply_text(
            "▶️**\n» ʀᴇꜱᴜᴍᴇᴅ**"
        )


@Client.on_message(command(["end", f"end@{BOT_USERNAME}", "stop", f"end@{BOT_USERNAME}"]) & other_filters)
@errors
@authorized_users_only
async def stop(_, message: Message):
    chat_id = get_chat_id(message.chat)
    ACTV_CALL = []
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALL.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALL:
        await message.reply_text("❌ **ɴᴏᴛʜɪɴɢ ɪꜱ ᴘʟᴀʏɪɴɢ**")
    else:
        try:
            queues.clear(chat_id)
        except QueueEmpty:
            pass
        await callsmusic.pytgcalls.leave_group_call(chat_id)
        await message.reply_text("✅ **ꜱᴛᴏᴘᴘᴇᴅ ʟᴇᴀᴠɪɴɢ ᴠᴄ ᴄʜᴀᴛ**")


@Client.on_message(command(["skip", f"skip@{BOT_USERNAME}", "next", f"next@{BOT_USERNAME}"]) & other_filters)
@errors
@authorized_users_only
async def skip(_, message: Message):
    global que
    chat_id = message.chat.id
    ACTV_CALLS = []
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALLS:
        await message.reply_text("❌ **ɴᴏᴛʜɪɴɢ ɪꜱ ᴘʟᴀʏɪɴɢ**")
    else:
        queues.task_done(chat_id)
        
        if queues.is_empty(chat_id):
            await callsmusic.pytgcalls.leave_group_call(chat_id)
        else:
            await callsmusic.pytgcalls.change_stream(
                chat_id, 
                InputStream(
                    InputAudioStream(
                        callsmusic.queues.get(chat_id)["file"],
                    ),
                ),
            )
                
    qeue = que.get(chat_id)
    if qeue:
        qeue.pop(0)
    if not qeue:
        return
    await message.reply_text("⏭ **ꜱᴋɪᴘᴘᴇᴅ ᴘʟᴀʏɪɴɢ ɴᴇxᴛ ꜱᴏɴɢ.**")


@Client.on_message(command(["auth", f"verify"]) & other_filters)
@authorized_users_only
async def authenticate(client, message):
    global admins
    if not message.reply_to_message:
        return await message.reply("💝 ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴛᴏ ᴠᴇʀɪꜰʏ !")
    if message.reply_to_message.from_user.id not in admins[message.chat.id]:
        new_admins = admins[message.chat.id]
        new_admins.append(message.reply_to_message.from_user.id)
        admins[message.chat.id] = new_admins
        await message.reply(
            "🟢 ʀᴇᴘʟɪᴇᴅ ᴜꜱᴇʀ ɴᴏᴡ ᴠᴇʀɪꜰɪᴇᴅ ɴᴏᴡ ᴄᴀɴ ᴇɴᴊᴏʏ ʟɪᴋᴇ ᴀᴅᴍɪɴꜱ."
        )
    else:
        await message.reply("✅ ᴛʜɪꜱ ᴜꜱᴇʀ ᴀʟʀᴇᴀᴅʏ ᴠᴇʀɪꜰɪᴇᴅ!")


@Client.on_message(command(["unauth", f"unverify"]) & other_filters)
@authorized_users_only
async def deautenticate(client, message):
    global admins
    if not message.reply_to_message:
        return await message.reply("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ!")
    if message.reply_to_message.from_user.id in admins[message.chat.id]:
        new_admins = admins[message.chat.id]
        new_admins.remove(message.reply_to_message.from_user.id)
        admins[message.chat.id] = new_admins
        await message.reply(
            "🔴ʀᴇᴘʟɪᴇᴅ ᴜꜱᴇʀ ɴᴏᴡ ᴜɴᴠᴇʀɪꜰɪᴇᴅ ɴᴏᴡ ᴄᴀɴ't ᴇɴᴊᴏʏ ʟɪᴋᴇ ᴀᴅᴍɪɴꜱ."
        )
    else:
        await message.reply("✅ ᴛʜɪꜱ ᴜꜱᴇʀ ᴀʟʀᴇᴀᴅʏ unᴠᴇʀɪꜰɪᴇᴅ!")


# this is a anti cmd feature
@Client.on_message(command(["delcmd", f"delcmd@{BOT_USERNAME}"]) & other_filters)
@authorized_users_only
async def delcmdc(_, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "read the /help message to know how to use this command"
        )
    status = message.text.split(None, 1)[1].strip()
    status = status.lower()
    chat_id = message.chat.id
    if status == "on":
        if await delcmd_is_on(message.chat.id):
            return await message.reply_text("✅ already activated")
        await delcmd_on(chat_id)
        await message.reply_text("🟢 activated successfully")
    elif status == "off":
        await delcmd_off(chat_id)
        await message.reply_text("🔴 disabled successfully")
    else:
        await message.reply_text(
            "read the /help message to know how to use this command"
        )


# music player callbacks (control by buttons feature)


@Client.on_callback_query(filters.regex("cbpause"))
async def cbpause(_, query: CallbackQuery):
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 only admin can tap this button !", show_alert=True)
    chat_id = get_chat_id(query.message.chat)
    ACTV_CALL = []
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALL.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALL:
        await query.edit_message_text(
            "❌ **no music is currently playing**", reply_markup=BACK_BUTTON
        )
    else:
        await callsmusic.pytgcalls.pause_stream(chat_id)
        await query.edit_message_text(
            "⏸ music playback has been paused", reply_markup=BACK_BUTTON
        )


@Client.on_callback_query(filters.regex("cbresume"))
async def cbresume(_, query: CallbackQuery):
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 only admin can tap this button !", show_alert=True)
    chat_id = get_chat_id(query.message.chat)
    ACTV_CALL = []
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALL.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALL:
        await query.edit_message_text(
            "❌ **no music is paused**", reply_markup=BACK_BUTTON
        )
    else:
        await callsmusic.pytgcalls.resume_stream(chat_id)
        await query.edit_message_text(
            "▶️ music playback has been resumed", reply_markup=BACK_BUTTON
        )


@Client.on_callback_query(filters.regex("cbend"))
async def cbend(_, query: CallbackQuery):
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 only admin can tap this button !", show_alert=True)
    chat_id = get_chat_id(query.message.chat)
    ACTV_CALL = []
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALL.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALL:
        await query.edit_message_text(
            "❌ **no music is currently playing**", reply_markup=BACK_BUTTON
        )
    else:
        try:
            queues.clear(chat_id)
        except QueueEmpty:
            pass
        
        await callsmusic.pytgcalls.leave_group_call(chat_id)
        await query.edit_message_text(
            "✅ the music queue has been cleared and successfully left voice chat",
            reply_markup=BACK_BUTTON,
        )


@Client.on_callback_query(filters.regex("cbskip"))
async def cbskip(_, query: CallbackQuery):
    global que
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 only admin can tap this button !", show_alert=True)
    chat_id = get_chat_id(query.message.chat)
    ACTV_CALLS = []
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALLS:
        await query.edit_message_text(
            "❌ **no music is currently playing**", reply_markup=BACK_BUTTON
        )
    else:
        queues.task_done(chat_id)
        
        if queues.is_empty(chat_id):
            await callsmusic.pytgcalls.leave_group_call(chat_id)
        else:
            await callsmusic.pytgcalls.change_stream(
                chat_id, 
                InputStream(
                    InputAudioStream(
                        queues.get(query.message.chat.id)["file"],
                    ),
                ),
            )

    qeue = que.get(chat_id)
    if qeue:
        qeue.pop(0)
    if not qeue:
        return
    await query.edit_message_text(
        "⏭ **You've skipped to the next song**", reply_markup=BACK_BUTTON
    )


@Client.on_message(command(["volume", f"sound"]) & other_filters)
@authorized_users_only
async def change_volume(client, message):
    range = message.command[1]
    chat_id = message.chat.id
    try:
       await callsmusic.pytgcalls.change_volume_call(chat_id, volume=int(range))
       await message.reply(f"✅ **volume set to:** ```{range}%```")
    except Exception as e:
       await message.reply(f"**error:** {e}")
