from base.player import player

from pyrogram import types, filters, Client

from solidAPI import get_message as gm

from utils.decorators import authorized_only
from utils.functions import group_only


@Client.on_message(filters.command("pause") & group_only)
@authorized_only
async def pause_(_, message: types.Message):
    await player.change_status("pause", message.chat.id)
    await message.reply(gm(message.chat.id, "track_paused"))


@Client.on_message(filters.command("resume") & group_only)
@authorized_only
async def resume_(_, message: types.Message):
    await player.change_status("resume", message.chat.id)
    await message.reply(gm(message.chat.id, "track_resumed"))


@Client.on_message(filters.command("skip") & group_only)
@authorized_only
async def skip_(_, msg: types.Message):
    x = await player.change_stream(msg.chat.id)
    await msg.reply(x)


@Client.on_message(filters.command("end") & group_only)
@authorized_only
async def end_(_, msg: types.Message):
    x = await player.end_stream(msg.chat.id)
    await msg.reply(x)


@Client.on_message(filters.command("vol") & group_only)
@authorized_only
async def change_vol_(_, message: types.Message):
    vol = int("".join(message.command[1]))
    await player.change_vol(message.chat.id, vol)
    await message.reply(gm(message.chat.id, "vol_changed").format(vol))
