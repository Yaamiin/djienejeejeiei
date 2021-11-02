from konfig import config
from pyrogram import Client
from pytgcalls import PyTgCalls

bot = Client(
    ":memory:",
    config.API_ID,
    config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins={"root": "handlers"},
)

user = Client(
    config.SESSION,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
)

call_py = PyTgCalls(user) if not config.MULTI_THREAD else PyTgCalls(user, multi_thread=True)
