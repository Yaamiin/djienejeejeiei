import asyncio
import shutil
import os

from pytgcalls import idle
from base.client_base import bot, call_py


if not os.path.exists("search"):
    os.mkdir("search")


async def mulai_bot():
    print("[INFO]: STARTING BOT CLIENT")
    await bot.start()
    print("[INFO]: STARTING PYTGCALLS CLIENT")
    await call_py.start()
    print("[INFO]: BOT RUNNING")
    await idle()
    print("[INFO]: STOPPING BOT")
    await bot.stop()
    if os.path.isdir("search"):
        shutil.rmtree("search")


loop = asyncio.get_event_loop()
loop.run_until_complete(mulai_bot())
