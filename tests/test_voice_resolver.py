import pytest

from aivis_openai_tts_bridge.voice_resolver import VoiceResolver


class TestVoiceResolver:
    @pytest.mark.asyncio
    async def test_resolve_style_id_direct(self, mock_aivis_client):
        resolver = VoiceResolver(mock_aivis_client)
        result = await resolver.resolve("123456")
        assert result == 123456

    @pytest.mark.asyncio
    async def test_resolve_empty_fallback_auto(self, voice_resolver, mock_settings):
        mock_settings.aivis.default_voice = "auto"
        result = await voice_resolver.resolve("")
        assert result == 100

    @pytest.mark.asyncio
    async def test_resolve_auto(self, voice_resolver, mock_settings):
        mock_settings.aivis.default_voice = "auto"
        result = await voice_resolver.resolve("auto")
        assert result == 100

    @pytest.mark.asyncio
    async def test_resolve_speaker_name(self, voice_resolver):
        result = await voice_resolver.resolve("SpeakerA")
        assert result == 100

    @pytest.mark.asyncio
    async def test_resolve_speaker_with_style(self, voice_resolver):
        result = await voice_resolver.resolve("SpeakerA:Happy")
        assert result == 101

    @pytest.mark.asyncio
    async def test_resolve_invalid_speaker(self, voice_resolver):
        with pytest.raises(ValueError, match="Speaker not found"):
            await voice_resolver.resolve("InvalidSpeaker")

    @pytest.mark.asyncio
    async def test_resolve_invalid_style(self, voice_resolver):
        with pytest.raises(ValueError, match="Style 'InvalidStyle' not found"):
            await voice_resolver.resolve("SpeakerA:InvalidStyle")

    @pytest.mark.asyncio
    async def test_resolve_invalid_speaker_with_style(self, voice_resolver):
        with pytest.raises(ValueError, match="Speaker not found: InvalidSpeaker"):
            await voice_resolver.resolve("InvalidSpeaker:SomeStyle")

    @pytest.mark.asyncio
    async def test_resolve_empty_default_voice(self, voice_resolver, mock_settings):
        mock_settings.aivis.default_voice = ""
        result = await voice_resolver.resolve("")
        assert result == 100

    @pytest.mark.asyncio
    async def test_resolve_default_voice_speaker(self, voice_resolver, mock_settings):
        mock_settings.aivis.default_voice = "SpeakerB"
        result = await voice_resolver.resolve("")
        assert result == 200

    @pytest.mark.asyncio
    async def test_resolve_default_voice_style_id(
        self, mock_aivis_client, mock_settings
    ):
        mock_settings.aivis.default_voice = "300"
        resolver = VoiceResolver(mock_aivis_client)
        result = await resolver.resolve("")
        assert result == 300
