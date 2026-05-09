import asyncio
import logging
import subprocess
import sys
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
)
from fastapi.exception_handlers import http_exception_handler
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from . import __version__
from .aivis_client import AivisClient
from .config import CLISettings, settings
from .voice_resolver import VoiceResolver

app = FastAPI(
    title="Aivis OpenAI TTS Bridge",
    description="OpenAI TTS API-compatible bridge for AivisSpeech Engine",
    version=__version__,
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    logging.warning(
        f"HTTP {exc.status_code} error for {request.method} {request.url.path}: {exc.detail}"
    )
    return await http_exception_handler(request, exc)


security = HTTPBearer(auto_error=False)


async def verify_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
):
    if settings.server.api_key:
        if not credentials or credentials.credentials != settings.server.api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return credentials


aivis_client = AivisClient()
voice_resolver = VoiceResolver(aivis_client)


class SpeechRequest(BaseModel):
    model: str
    input: str
    voice: str
    response_format: str = "wav"
    speed: float = 1.0


FFMPEG_FORMATS = {
    "mp3": ("audio/mpeg", ["-f", "mp3", "-ab", "192k"]),
    "opus": ("audio/ogg", ["-f", "ogg", "-c:a", "libopus", "-b:a", "128k"]),
    "aac": ("audio/aac", ["-f", "adts", "-c:a", "aac", "-b:a", "192k"]),
    "flac": ("audio/flac", ["-f", "flac"]),
    "wav": ("audio/wav", []),
    "pcm": ("audio/raw", ["-f", "s16le"]),
}


async def convert_audio(audio_data: bytes, format: str) -> bytes:
    if format == "wav":
        return audio_data
    media_type, ffmpeg_args = FFMPEG_FORMATS.get(format, (None, None))
    if media_type is None or ffmpeg_args is None:
        raise ValueError(f"Unsupported format: {format}")
    result = await asyncio.to_thread(
        subprocess.run,
        ["ffmpeg", "-f", "wav", "-i", "pipe:0"] + ffmpeg_args + ["pipe:1"],
        input=audio_data,
        capture_output=True,
        text=False,
        check=True,
    )
    stdout = result.stdout
    if isinstance(stdout, str):
        raise RuntimeError("Unexpected text output from ffmpeg")
    return stdout


class ModelResponse(BaseModel):
    id: str
    object: str = "model"
    created: int = 1700000000
    owned_by: str = "aivis"


@app.get("/")
async def root():
    return {
        "message": "Aivis OpenAI TTS Bridge is running",
        "docs": "/docs",
        "version": __version__,
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/v1/models")
async def list_models(
    _auth: Annotated[
        HTTPAuthorizationCredentials | None, Depends(verify_api_key)
    ] = None,
):
    return {
        "object": "list",
        "data": [
            ModelResponse(id="aivis-tts-1"),
        ],
    }


@app.get("/v1/voices")
async def list_voices(
    _auth: Annotated[
        HTTPAuthorizationCredentials | None, Depends(verify_api_key)
    ] = None,
):
    speakers = await aivis_client.get_speakers()
    voices = []
    for speaker in speakers:
        for style in speaker.get("styles", []):
            voices.append(
                {
                    "id": str(style["id"]),
                    "name": f"{speaker['name']}:{style['name']}",
                    "speaker": speaker["name"],
                    "style": style["name"],
                }
            )
    return {"object": "list", "data": voices}


@app.post("/v1/audio/speech")
async def create_speech(
    request: SpeechRequest,
    _auth: Annotated[
        HTTPAuthorizationCredentials | None, Depends(verify_api_key)
    ] = None,
):
    logging.info(f"TTS request: voice={request.voice}, input={request.input[:50]}...")
    try:
        speaker_id = await voice_resolver.resolve(request.voice)
    except ValueError as e:
        logging.warning(f"Voice resolution failed for '{request.voice}': {e}")
        raise HTTPException(status_code=400, detail=str(e)) from None

    try:
        audio_data = await aivis_client.tts(request.input, speaker_id, request.speed)
    except Exception as e:
        logging.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None

    if request.response_format not in FFMPEG_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported response format: {request.response_format}",
        )

    try:
        converted = await convert_audio(audio_data, request.response_format)
        media_type = FFMPEG_FORMATS[request.response_format][0]
        return Response(content=converted, media_type=media_type)
    except subprocess.CalledProcessError as e:
        logging.error(f"Audio conversion failed: {e.stderr.decode()}")
        raise HTTPException(
            status_code=500,
            detail="Audio conversion failed",
        ) from None
    except FileNotFoundError:
        logging.error("ffmpeg not found")
        raise HTTPException(
            status_code=500,
            detail="ffmpeg not found, audio conversion unavailable",
        ) from None


def main():
    if len(sys.argv) == 1:
        print("aivis-openai-tts-bridge - Aivis OpenAI TTS Bridge")
        print("\nUsage: aivis-openai-tts-bridge serve [options]")
        print("\nOptions:")
        print("  --aivis.url URL           AivisSpeech Engine URL")
        print("  --aivis.default-voice VOICE  Default voice (auto|speaker|style_id)")
        print("  --server.host HOST        Bind host")
        print("  --server.port PORT        Bind port")
        print("  --server.debug            Enable debug mode")
        print("  --server.api-key KEY      API key for authentication")
        sys.exit(0)

    if sys.argv[1] == "serve":
        sys.argv.pop(1)
        cli_settings = CLISettings()

        if cli_settings.server.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("Debug logging enabled")

        import uvicorn

        uvicorn.run(
            app,
            host=cli_settings.server.host,
            port=cli_settings.server.port,
        )
    elif sys.argv[1] in ("-h", "--help", "help"):
        print("aivis-openai-tts-bridge - Aivis OpenAI TTS Bridge")
        print("\nUsage: aivis-openai-tts-bridge serve [options]")
        print("\nOptions:")
        print("  --aivis.url URL           AivisSpeech Engine URL")
        print("  --aivis.default-voice VOICE  Default voice (auto|speaker|style_id)")
        print("  --server.host HOST        Bind host")
        print("  --server.port PORT        Bind port")
        print("  --server.debug            Enable debug mode")
        print("  --server.api-key KEY      API key for authentication")
        sys.exit(0)
    else:
        print(f"Unknown command: {sys.argv[1]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
