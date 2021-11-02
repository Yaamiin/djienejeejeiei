from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from solidAPI import emoji, get_sudos
from solidAPI.chat import add_chat, set_lang
from solidAPI.other import get_message as gm

from base.player import player
from utils.functions import res_music
from utils.pyro_utils import music_result


def play_next_keyboard(user_id: int):
    i = 5
    for j in range(5):
        i += 1
        yield InlineKeyboardButton(f"{i}", callback_data=f"nextplay {j}|{user_id}")
        j += 1


def play_back_keyboard(user_id: int):
    i = 0
    for j in range(5):
        i += 1
        yield InlineKeyboardButton(f"{i}", callback_data=f"play {j}|{user_id}")
        j += 1


async def edit_inline_text(
    inline_board: list[InlineKeyboardButton],
    temp: list,
    keyboard: list,
    cb: CallbackQuery,
    user_id: int,
    stats: str,
    k: int,
    music: list,
    bot_username: str,
):
    chat_id = cb.message.chat.id
    results = res_music(k, music, bot_username, chat_id)
    for count, j in enumerate(inline_board, start=1):
        temp.append(j)
        if count % 3 == 0:
            keyboard.append(temp)
            temp = []
        if count == len(inline_board):
            keyboard.append(temp)
    await cb.edit_message_text(
        f"{results}",
        reply_markup=InlineKeyboardMarkup(
            [
                keyboard[0],
                keyboard[1],
                [
                    InlineKeyboardButton(f"{emoji.RIGHT_ARROW}", f"next|{user_id}")
                    if stats == "next"
                    else InlineKeyboardButton(
                        f"{emoji.LEFT_ARROW}", callback_data=f"back|{user_id}"
                    ),
                    InlineKeyboardButton(
                        f"{gm(chat_id, 'close_btn_name')} {emoji.WASTEBASKET}", f"close|{user_id}"
                    ),
                ],
            ]
        ),
        disable_web_page_preview=True,
    )


async def play_music(cb, music, index, chat_id, user_id):
    title: str = music[index]["title"]
    uri: str = music[index]["url"]
    duration = music[index]["duration"]
    yt_id = music[index]["id"]
    result = {"title": title, "uri": uri, "duration": duration, "user_id": user_id, "yt_id": yt_id}
    music_result[chat_id].clear()
    await player.play(cb, result)


async def get_infos(client, cb, k):
    bot_username = (await client.get_me()).username
    chat_id = cb.message.chat.id
    user_id = int(cb.data.split("|")[1])
    music = music_result[chat_id][k]
    return bot_username, user_id, music


@Client.on_callback_query(filters.regex(pattern=r"close"))
async def close_button(_, cb: CallbackQuery):
    callback = cb.data.split("|")
    user_id = int(callback[1])
    message = cb.message
    from_user_id = cb.from_user.id
    chat_id = message.chat.id
    person = await message.chat.get_member(from_user_id)
    if from_user_id != user_id:
        return await cb.answer(gm(chat_id, "not_for_you"), show_alert=True)
    music_result[chat_id].clear()
    if person.status in ["creator", "administrator", get_sudos(chat_id)]:
        return await message.delete()
    return await message.delete()


@Client.on_callback_query(filters.regex(pattern=r"cls"))
async def close_private_button(_, cb: CallbackQuery):
    return await cb.message.delete()


@Client.on_callback_query(filters.regex(pattern=r"set_lang_(.*)"))
async def change_language_(_, cb: CallbackQuery):
    lang = cb.matches[0].group(1)
    chat = cb.message.chat
    try:
        set_lang(chat.id, lang)
        await cb.edit_message_text(gm(chat.id, "lang_changed"))
    except KeyError:
        add_chat(chat.id, lang)
        await cb.edit_message_text(gm(chat.id, "lang_changed"))


@Client.on_callback_query(filters.regex(pattern=r"(.*)play"))
async def play_music_(_, cb: CallbackQuery):
    match = cb.matches[0].group(1)
    data = cb.data.split("|")
    user_id = int(data[1])
    index = int(data[0].split(" ")[1])
    chat_id = cb.message.chat.id
    from_id = cb.from_user.id
    if from_id != user_id:
        return await cb.answer(gm(chat_id, "not_for_you"), show_alert=True)
    if not match:
        music = music_result[chat_id][0]
        await play_music(cb, music, index, chat_id, user_id)
    if match:
        music = music_result[chat_id][1]
        await play_music(cb, music, index, chat_id, user_id)


@Client.on_callback_query(filters.regex(pattern=r"next"))
async def next_music_(client: Client, cb: CallbackQuery):
    bot_username, user_id, music = await get_infos(client, cb, 1)
    from_id = cb.from_user.id
    chat_id = cb.message.chat.id
    if from_id != user_id:
        return await cb.answer(gm(chat_id, "not_for_you"), show_alert=True)
    k = 5
    temp = []
    keyboard = []
    inline_board = list(play_next_keyboard(user_id))
    await edit_inline_text(
        inline_board, temp, keyboard, cb, user_id, "back", k, music, bot_username
    )


@Client.on_callback_query(filters.regex(pattern=r"back"))
async def back_music_(client: Client, cb: CallbackQuery):
    bot_username, user_id, music = await get_infos(client, cb, 0)
    from_id = cb.from_user.id
    chat_id = cb.message.chat.id
    if from_id != user_id:
        return await cb.answer(gm(chat_id, "not_for_you"), show_alert=True)
    k = 0
    temp = []
    keyboard = []
    inline_board = list(play_back_keyboard(user_id))
    await edit_inline_text(
        inline_board, temp, keyboard, cb, user_id, "next", k, music, bot_username
    )
