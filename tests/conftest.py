from unittest.mock import AsyncMock

import pytest

from aivis_openai_tts_bridge.aivis_client import AivisClient
from aivis_openai_tts_bridge.voice_resolver import VoiceResolver

MOCK_SPEAKERS = [
    {
        "name": "SpeakerA",
        "speaker_uuid": "uuid-a",
        "styles": [
            {"name": "Normal", "id": 100},
            {"name": "Happy", "id": 101},
        ],
        "version": "1.0.0",
    },
    {
        "name": "SpeakerB",
        "speaker_uuid": "uuid-b",
        "styles": [
            {"name": "Default", "id": 200},
        ],
        "version": "1.0.0",
    },
]


@pytest.fixture(autouse=True)
def mock_settings(mocker):
    from aivis_openai_tts_bridge.config import Settings

    settings = Settings()
    settings.aivis.url = "http://dummy-upstream:0"
    mocker.patch("aivis_openai_tts_bridge.main.settings", settings)
    mocker.patch("aivis_openai_tts_bridge.voice_resolver.settings", settings)
    return settings


@pytest.fixture(autouse=True)
def mock_main_client(mocker, mock_settings):
    mock_client = mocker.patch("aivis_openai_tts_bridge.main.aivis_client")
    mock_client.base_url = mock_settings.aivis.url
    mock_client.get_speakers = AsyncMock(return_value=MOCK_SPEAKERS)
    mock_client.tts = AsyncMock(return_value=b"RIFF\x00\x00\x00\x00WAVE")
    mocker.patch(
        "aivis_openai_tts_bridge.main.voice_resolver.client",
        mock_client,
    )
    return mock_client


@pytest.fixture
def mock_aivis_client(mocker):
    client = AivisClient()
    mocker.patch.object(client, "get_speakers", AsyncMock(return_value=MOCK_SPEAKERS))
    mocker.patch.object(
        client, "tts", AsyncMock(return_value=b"RIFF\x00\x00\x00\x00WAVE")
    )
    return client


@pytest.fixture
def voice_resolver(mock_aivis_client):
    return VoiceResolver(mock_aivis_client)
