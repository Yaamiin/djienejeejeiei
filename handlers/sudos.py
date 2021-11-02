from pyrogram import Client, filters, types

from solidAPI.sudo import add_sudo, get_sudos, del_sudo, put_sudo
from solidAPI import get_message

from utils.decorators import authorized_only
from utils.functions import group_only


def check_sudo_id(message: types.Message):
    msg_cmd = message.command[1]
    try:
        sudo_id = int(msg_cmd)
    except IndexError:
        sudo_id = ""
    except ValueError:
        if msg_cmd.startswith("@"):
            sudo_id = msg_cmd
        else:
            sudo_id = ""
    return sudo_id


async def update_sudo(message: types.Message, chat_id: int, sudo_id: int, status: str):
    mention_user = (await message.chat.get_member(sudo_id)).user.mention
    all_sudos = get_sudos(chat_id)
    if status == "add":
        if all_sudos:
            if sudo_id in all_sudos:
                x = put_sudo(chat_id, sudo_id)
                status = x["status"]
                if status == 200:
                    return get_message(chat_id, "added_sudo")
                if status == 400:
                    return get_message(chat_id, "already_become_sudo")
                return
            return
        x = add_sudo(chat_id, sudo_id)
        if x == 200:
            return get_message(chat_id, "added_sudo")
        if x == 400:
            return get_message(chat_id, "already_become_sudo")
        return
    if status == "delete":
        x = del_sudo(chat_id, sudo_id)
        if x == 200:
            return get_message(chat_id, "deleted_sudo")
        if x == 404:
            return get_message(chat_id, "already_deleted_sudo")
        return


async def process_sudo_update(message: types.Message, status: str):
    sudo_id = check_sudo_id(message)
    replied = message.reply_to_message
    chat_id = message.chat.id
    if status == "add":
        if not replied:
            if isinstance(sudo_id, int):
                res = await update_sudo(message, chat_id, sudo_id, "add")
                return await message.reply(res)
            if isinstance(sudo_id, str) and len(sudo_id) >= 1:
                user_id = (await message.chat.get_member(sudo_id)).user.id
                res = await update_sudo(message, chat_id, user_id, "add")
                return await message.reply(res)
        elif replied:
            user_id = replied.from_user.id
            res = await update_sudo(message, chat_id, user_id, "add")
            return await message.reply(res)
    elif status == "delete":
        if not replied:
            if isinstance(sudo_id, int):
                res = await update_sudo(message, chat_id, sudo_id, "delete")
                return await message.reply(res)
            if isinstance(sudo_id, str) and len(sudo_id) >= 1:
                user_id = (await message.chat.get_member(sudo_id)).user.id
                res = await update_sudo(message, chat_id, user_id, "delete")
                return await message.reply(res)
        elif replied:
            user_id = replied.from_user.id
            res = await update_sudo(message, chat_id, user_id, "delete")
            return await message.reply(res)


@Client.on_message(filters.command("addsudo") & group_only)
@authorized_only
async def add_sudos_(_, message: types.Message):
    await process_sudo_update(message, "add")


@Client.on_message(filters.command("delsudo") & group_only)
@authorized_only
async def del_sudo_(_, message: types.Message):
    await process_sudo_update(message, "delete")
