# aivis-openai-tts-bridge

OpenAI TTS API-compatible bridge for AivisSpeech Engine / VOICEVOX.

## Quick Start (Docker)

```bash
# Download .env.example
curl -o .env.example https://github.com/likeablob/aivis-openai-tts-bridge/raw/refs/heads/main/.env.example

# Edit .env to configure AivisSpeech Engine URL
cp .env.example .env
editor .env

# Create compose.yaml
cat << 'EOF' > compose.yaml
services:
  tts-bridge:
    image: ghcr.io/likeablob/aivis-openai-tts-bridge:latest
    ports:
      - "10201:10201"
    env_file:
      - .env
    environment:
      - SERVER__HOST=0.0.0.0
      - SERVER__PORT=10201
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF

# Start the server
docker compose up -d
```

The API will be available at http://localhost:10201.

## Example setup with AivisSpeech Engine

Example `compose.yaml` with the AivisSpeech Engine container:

```yaml
x-logging: &logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"

services:
  aivis-engine:
    image: ghcr.io/aivis-project/aivisspeech-engine:nvidia-1.2.0
    # image: ghcr.io/aivis-project/aivisspeech-engine:cpu-1.2.0
    container_name: aivis-engine
    ports:
      - "10101:10101"
    volumes:
      - ./aivis-data:/home/user/.local/share/AivisSpeech-Engine-Dev
    environment:
      - TZ=Asia/Tokyo
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    logging: *logging
    restart: unless-stopped

  tts-bridge:
    image: ghcr.io/likeablob/aivis-openai-tts-bridge:latest
    container_name: tts-bridge
    ports:
      - "10201:10201"
    environment:
      - AIVIS__URL=http://aivis-engine:10101
      - SERVER__HOST=0.0.0.0
      - SERVER__PORT=10201
    depends_on:
      - aivis-engine
    logging: *logging
    restart: unless-stopped
```

## API Endpoints

- `POST /v1/audio/speech` - Text-to-speech (OpenAI compatible)
- `GET /v1/models` - List available models
- `GET /v1/voices` - List available voices
- `GET /health` - Health check

## Voice Resolution

Voice parameter supports:
- `"auto"` or empty: Uses default voice from config (first available if `AIVIS__DEFAULT_VOICE=auto`)
- Speaker name: `voice="SpeakerName"` (uses first style)
- Speaker + style: `voice="SpeakerName:StyleName"`
- Style ID directly: `voice="12345678"`

## Response Formats

OpenAI TTS API compatible formats:
- `wav` (default) - Direct AivisSpeech output, no conversion overhead
- `mp3` - Converted via ffmpeg (192kbps)
- `opus` - Converted via ffmpeg (128kbps, in Ogg container)
- `aac` - Converted via ffmpeg (192kbps)
- `flac` - Converted via ffmpeg (lossless)
- `pcm` - Converted via ffmpeg (raw 16-bit PCM)

## Example Request

```bash
curl -X POST http://localhost:10201/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"aivis-tts-1","input":"東京特許許可局局長","voice":"auto"}' \
  --output audio.wav
```

## Configuration

See [.env.example](.env.example) for configuration options.

## Development

```bash
# Install tools
mise trust .
mise install

# Install dependencies
uv sync --group dev

# Install pre-commit hooks
uv run pre-commit install

# Run linting
uv run ruff check

# Run type checking
uv run ty check src/

# Run tests
uv run pytest tests/

# Run server locally
uv run aivis-openai-tts-bridge serve
```

## LICENSE

MIT
