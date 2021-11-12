import requests
from pytgcalls import idle
from callsmusic import run
from handlers import __version__
from pyrogram import Client as Bot
from config import API_HASH, API_ID, BG_IMAGE, BOT_TOKEN


response = requests.get(BG_IMAGE)
with open("./etc/foreground.png", "wb") as file:
    file.write(response.content)


bot = Bot(
    ":memory:",
    API_ID,
    API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="zaidmusic"),
)

print(f"[INFO]: ZAID MUSIC VERSION 2.0 STARTED !")

bot.start()
run()
idle()
