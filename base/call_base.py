import random

from pyrogram.raw.functions.phone import CreateGroupCall
from pytgcalls.exceptions import GroupCallNotFound
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped
from solidAPI import get_message

from utils.functions import get_audio_link

from .client_base import call_py, user, bot


class CallBase:
    def __init__(self):
        self._user = user
        self._call = call_py
        self._bot = bot
        self._playlist: dict[int, list[dict[str, str]]] = {}

        @self._call.on_stream_end()
        async def stream_ended(_, update: Update):
            playlist = self._playlist
            chat_id = update.chat_id
            if len(playlist[chat_id]) > 1:
                playlist[chat_id].pop(0)
                query = playlist[chat_id][0]["uri"]
                await self.stream_change(chat_id, query)
            else:
                await self.leave_group_call(chat_id)
                del playlist[chat_id]

    async def create_call(self, chat_id: int):
        await self._user.send(
            CreateGroupCall(
                peer=await self._user.resolve_peer(chat_id),
                random_id=random.randint(10000, 999999999),
            )
        )

    async def leave_group_call(self, chat_id: int):
        return await self._call.leave_group_call(chat_id)

    async def change_status(self, status: str, chat_id: int):
        if status == "pause":
            call = self._call
            if call.get_call(chat_id):
                await call.pause_stream(chat_id)
        elif status == "resume":
            call = self._call
            if call.get_call(chat_id):
                await call.resume_stream(chat_id)

    async def change_vol(self, chat_id: int, vol: int):
        call = self._call
        if call.get_call(chat_id):
            await call.change_volume_call(chat_id, vol)

    async def stream_change(self, chat_id: int, query: str):
        call = self._call
        url = get_audio_link(query)
        await call.change_stream(chat_id, AudioPiped(url))

    async def change_stream(self, chat_id):
        playlist = self._playlist
        if len(playlist[chat_id]) > 1:
            playlist[chat_id].pop(0)
            query = playlist[chat_id][0]["uri"]
            title = playlist[chat_id][0]["title"]
            await self.stream_change(chat_id, query)
            return get_message(chat_id, "track_skipped").format(query)
        if not playlist:
            return get_message(chat_id, "no_playlists")

    async def end_stream(self, chat_id):
        playlist = self._playlist
        call = self._call
        try:
            if call.get_call(chat_id):
                await self.leave_group_call(chat_id)
                del playlist[chat_id]
                return get_message(chat_id, "track_ended")
        except GroupCallNotFound:
            return get_message(chat_id, "not_playing")

    def send_playlist(self, chat_id: int):
        playlist = self._playlist
        current = playlist[chat_id][0]
        queued = playlist[chat_id][1:]
        return current, queued
