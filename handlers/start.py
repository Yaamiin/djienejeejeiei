from pyrogram import Client, filters, types
from solidAPI import emoji, add_chat, get_message as gm

from base.client_base import bot
from utils.functions import get_yt_details, download_yt_thumbnails

markup_keyboard = types.InlineKeyboardMarkup
button_keyboard = types.InlineKeyboardButton


@Client.on_message(filters.command("start"))
async def start_(_, message: types.Message):
    bot_username = (await bot.get_me()).username
    chat_id = message.chat.id
    user_id = message.from_user.id
    lang = message.from_user.language_code
    mention = message.from_user.mention
    bot_name = f"{(await bot.get_me()).first_name} {(await bot.get_me()).last_name}"
    add_chat(chat_id, lang)
    if message.chat.type == "supergroup":
        return await message.reply(
            gm(chat_id, "chat_greet").format(mention, bot_name)
        )
    if message.chat.type == "private":
        if len(message.command) == 1:
            await message.reply(
                gm(chat_id, "pm_greet").format(mention),
                reply_markup=markup_keyboard(
                    [
                        [
                            button_keyboard(
                                gm(chat_id, "add_to_chat"),
                                url=f"https://t.me/{bot_username}?startgroup=true")
                        ],
                        [
                            button_keyboard(
                                f"{emoji.NOTEBOOK} commands",
                                callback_data="help_commands"
                            )
                        ],
                        [
                            button_keyboard(
                                f"{emoji.LOUDSPEAKER} channel",
                                url="https://t.me/solidprojects"
                            )
                        ],
                        [
                            button_keyboard(
                                f"{emoji.FIRE} {gm(chat_id, 'maintainer')}",
                                url="https://t.me/talktome_bbot"
                            )
                        ]
                    ]
                )
            )
        elif len(message.command) == 2:
            query = message.command[1]
            if query.startswith("ytinfo_"):
                yt_link = query.split("ytinfo_")[1]
                details = get_yt_details(yt_link)
                thumb_url = details["thumbnails"]
                thumb_file = download_yt_thumbnails(thumb_url, user_id)
                result_text = (
                    f"**{gm(chat_id, 'track_info')}**\n\n"
                    f"{emoji.LABEL} **{gm(chat_id, 'yt_title')}**: {details['title']}\n"
                    f"{emoji.MEGAPHONE} **channel**: {details['channel']}\n"
                    f"{emoji.STOPWATCH} **{gm(chat_id, 'duration')}**: {details['duration']}\n"
                    f"{emoji.THUMBS_UP} **{gm(chat_id, 'yt_likes')}**: {details['likes']}\n"
                    f"{emoji.THUMBS_DOWN} **{gm(chat_id, 'yt_dislikes')}**: {details['dislikes']}\n"
                    f"{emoji.STAR} **{gm(chat_id, 'yt_rating')}**: {details['rating']}\n"
                )
                await message.reply_photo(
                    thumb_file, caption=result_text, reply_markup=markup_keyboard(
                        [
                            [
                                button_keyboard(
                                    f"{emoji.MOVIE_CAMERA} {gm(chat_id, 'watch_on_yt')}",
                                    url=f"{details['link']}"
                                )
                            ],
                            [
                                button_keyboard(
                                    f"{emoji.WASTEBASKET} {gm(chat_id, 'close_btn_name')}",
                                    callback_data="cls"
                                )
                            ]
                        ]
                    )
                )
