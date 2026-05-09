import logging

import httpx

from .config import settings

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class AivisClient:
    def __init__(self):
        self.base_url = settings.aivis.url.rstrip("/")
        self._speakers_cache: list[dict] | None = None

    async def get_speakers(self) -> list[dict]:
        if self._speakers_cache is not None:
            return self._speakers_cache

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(f"{self.base_url}/speakers")
            resp.raise_for_status()
            self._speakers_cache = resp.json()
            return self._speakers_cache

    async def create_audio_query(self, text: str, speaker: int) -> dict:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.post(
                f"{self.base_url}/audio_query",
                params={"text": text, "speaker": speaker},
            )
            resp.raise_for_status()
            return resp.json()

    async def synthesis(self, query: dict, speaker: int) -> bytes:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.post(
                f"{self.base_url}/synthesis",
                params={"speaker": speaker},
                json=query,
            )
            resp.raise_for_status()
            return resp.content

    async def tts(self, text: str, speaker: int, speed: float = 1.0) -> bytes:
        query = await self.create_audio_query(text, speaker)
        query["speedScale"] = speed
        logging.debug(f"Audio query created with speed={speed}")
        return await self.synthesis(query, speaker)

    def invalidate_cache(self):
        self._speakers_cache = None
