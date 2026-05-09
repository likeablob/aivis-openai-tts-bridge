import pytest
from fastapi.testclient import TestClient

from aivis_openai_tts_bridge.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert "version" in data


def test_list_models(client):
    resp = client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "list"
    assert len(data["data"]) >= 1


class TestSpeechEndpoint:
    def test_speech_with_auto_voice(self, client, mock_main_client, mock_settings):
        mock_settings.aivis.default_voice = "auto"
        resp = client.post(
            "/v1/audio/speech",
            json={"model": "aivis-tts-1", "input": "test", "voice": "auto"},
        )
        assert resp.status_code == 200
        assert resp.content.startswith(b"RIFF")

    def test_speech_with_style_id(self, client, mock_main_client):
        resp = client.post(
            "/v1/audio/speech",
            json={"model": "aivis-tts-1", "input": "test", "voice": "123456"},
        )
        assert resp.status_code == 200
        mock_main_client.tts.assert_called_once_with("test", 123456, 1.0)

    def test_speech_with_speaker_name(self, client, mock_main_client):
        resp = client.post(
            "/v1/audio/speech",
            json={"model": "aivis-tts-1", "input": "test", "voice": "SpeakerA"},
        )
        assert resp.status_code == 200
        mock_main_client.tts.assert_called_once_with("test", 100, 1.0)

    def test_speech_invalid_voice(self, client, mock_main_client):
        from unittest.mock import AsyncMock

        mock_main_client.get_speakers = AsyncMock(return_value=[])

        resp = client.post(
            "/v1/audio/speech",
            json={"model": "aivis-tts-1", "input": "test", "voice": "Invalid"},
        )
        assert resp.status_code == 400

    def test_speech_tts_error(self, client, mock_main_client):
        from unittest.mock import AsyncMock

        mock_main_client.tts = AsyncMock(side_effect=Exception("TTS failed"))

        resp = client.post(
            "/v1/audio/speech",
            json={"model": "aivis-tts-1", "input": "test", "voice": "123456"},
        )
        assert resp.status_code == 500

    def test_speech_mp3_format(self, client, mock_main_client, mocker):
        mock_subprocess = mocker.patch("aivis_openai_tts_bridge.main.subprocess.run")
        mock_subprocess.return_value.stdout = b"ID3"

        resp = client.post(
            "/v1/audio/speech",
            json={
                "model": "aivis-tts-1",
                "input": "test",
                "voice": "123456",
                "response_format": "mp3",
            },
        )
        assert resp.status_code == 200

    def test_speech_invalid_format(self, client, mock_main_client):
        resp = client.post(
            "/v1/audio/speech",
            json={
                "model": "aivis-tts-1",
                "input": "test",
                "voice": "123456",
                "response_format": "invalid_format",
            },
        )
        assert resp.status_code == 400


class TestVoicesEndpoint:
    def test_list_voices(self, client, mock_main_client):
        resp = client.get("/v1/voices")
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 3


class TestApiKey:
    def test_no_api_key_required(self, client, mock_main_client, mocker):
        mock_settings = mocker.patch("aivis_openai_tts_bridge.main.settings")
        mock_settings.server.api_key = None

        resp = client.post(
            "/v1/audio/speech",
            json={"model": "aivis-tts-1", "input": "test", "voice": "123456"},
        )
        assert resp.status_code == 200

    def test_api_key_valid(self, client, mock_main_client, mocker):
        mock_settings = mocker.patch("aivis_openai_tts_bridge.main.settings")
        mock_settings.server.api_key = "secret-key"

        resp = client.post(
            "/v1/audio/speech",
            json={"model": "aivis-tts-1", "input": "test", "voice": "123456"},
            headers={"Authorization": "Bearer secret-key"},
        )
        assert resp.status_code == 200

    def test_api_key_missing(self, client, mocker):
        mock_settings = mocker.patch("aivis_openai_tts_bridge.main.settings")
        mock_settings.server.api_key = "secret-key"

        resp = client.post(
            "/v1/audio/speech",
            json={"model": "aivis-tts-1", "input": "test", "voice": "123456"},
        )
        assert resp.status_code == 401

    def test_api_key_invalid(self, client, mocker):
        mock_settings = mocker.patch("aivis_openai_tts_bridge.main.settings")
        mock_settings.server.api_key = "secret-key"

        resp = client.post(
            "/v1/audio/speech",
            json={"model": "aivis-tts-1", "input": "test", "voice": "123456"},
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert resp.status_code == 401
