import logging

from .config import settings


class VoiceResolver:
    def __init__(self, aivis_client):
        self.client = aivis_client

    async def resolve(self, voice: str) -> int:
        if not voice or voice == "auto":
            return await self._resolve_default_voice()

        if voice.isdigit():
            return int(voice)

        if ":" in voice:
            speaker_name, style_name = voice.split(":", 1)
            return await self._resolve_by_speaker_and_style(
                speaker_name.strip(), style_name.strip()
            )

        return await self._resolve_by_speaker_name(voice.strip())

    async def _resolve_default_voice(self) -> int:
        default_voice = settings.aivis.default_voice
        if not default_voice or default_voice == "auto":
            speakers = await self.client.get_speakers()
            if speakers:
                styles = speakers[0].get("styles", [])
                if styles:
                    style_id = styles[0]["id"]
                    logging.info(f"Auto-selected first voice: style_id={style_id}")
                    return style_id
            raise ValueError("No speakers available for auto selection")
        return await self.resolve(default_voice)

    async def _resolve_by_speaker_name(self, name: str) -> int:
        speakers = await self.client.get_speakers()
        for speaker in speakers:
            if speaker["name"] == name:
                styles = speaker.get("styles", [])
                if styles:
                    default_style = styles[0]
                    logging.debug(
                        f"Resolved voice '{name}' to style_id={default_style['id']}"
                    )
                    return default_style["id"]

        raise ValueError(f"Speaker not found: {name}")

    async def _resolve_by_speaker_and_style(
        self, speaker_name: str, style_name: str
    ) -> int:
        speakers = await self.client.get_speakers()
        for speaker in speakers:
            if speaker["name"] == speaker_name:
                for style in speaker.get("styles", []):
                    if style["name"] == style_name:
                        logging.debug(
                            f"Resolved voice '{speaker_name}:{style_name}' to style_id={style['id']}"
                        )
                        return style["id"]
                raise ValueError(
                    f"Style '{style_name}' not found for speaker '{speaker_name}'"
                )

        raise ValueError(f"Speaker not found: {speaker_name}")
