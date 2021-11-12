import asyncio
from callsmusic.callsmusic import client as USER
from config import BOT_USERNAME, SUDO_USERS, GROUP_SUPPORT
from helpers.decorators import authorized_users_only, sudo_users_only, errors
from helpers.filters import command
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant


@Client.on_message(
    command(["join", f"userbotjoin"]) & ~filters.private & ~filters.bot
)
@authorized_users_only
@errors
async def join_group(client, message):
    chid = message.chat.id
    try:
        invitelink = await client.export_chat_invite_link(chid)
    except:
        await message.reply_text(
            "• **i'm not have permission:**\n\n» ❌ __Add Users__",
        )
        return

    try:
        user = await USER.get_me()
    except:
        user.first_name = "music assistant"

    try:
        await USER.join_chat(invitelink)
    except UserAlreadyParticipant:
        pass
    except Exception as e:
        print(e)
        await message.reply_text(
            f"🔴 **ꜰʟᴏᴏᴅ ᴡᴀɪᴛ ᴇʀʀᴏʀ** 🔴 \n\n**ʜᴇʟᴘᴇʀ ᴜꜱᴇʀʙᴏᴛ ᴜɴᴀʙʟᴇ ᴛᴏ ᴊᴏɪɴ ᴜʀ ᴄʜᴀᴛ @{ASSISTANT_NAME} ᴘʟᴢ ᴀᴅᴅ ᴍᴀɴᴜᴀʟʟʏ .**"
            f"\n\n**ᴏʀ ᴄᴏɴᴛᴀᴄᴛ @{GROUP_SUPPORT}.**",
        )
        return
    await message.reply_text(
        f"✅ **userbot succesfully entered chat**",
    )


@Client.on_message(
    command(["leave", f"leave@{BOT_USERNAME}"]) & filters.group & ~filters.edited
)
@authorized_users_only
async def leave_group(client, message):
    try:
        await USER.send_message(message.chat.id, "✅ userbot successfully left chat")
        await USER.leave_chat(message.chat.id)
    except:
        await message.reply_text(
            "❌ **userbot couldn't leave your group, may be floodwaits.**\n\n**» or manually kick userbot from your group**"
        )

        return


@Client.on_message(command(["leaveall", f"leaveall@{BOT_USERNAME}"]))
@sudo_users_only
async def leave_all(client, message):
    if message.from_user.id not in SUDO_USERS:
        return

    left = 0
    failed = 0
    lol = await message.reply("🔄 **userbot** leaving all chats !")
    async for dialog in USER.iter_dialogs():
        try:
            await USER.leave_chat(dialog.chat.id)
            left += 1
            await lol.edit(
                f"Userbot leaving all group...\n\nLeft: {left} chats.\nFailed: {failed} chats."
            )
        except:
            failed += 1
            await lol.edit(
                f"Userbot leaving...\n\nLeft: {left} chats.\nFailed: {failed} chats."
            )
        await asyncio.sleep(0.7)
    await client.send_message(
        message.chat.id, f"✅ Left from: {left} chats.\n❌ Failed in: {failed} chats."
    )
