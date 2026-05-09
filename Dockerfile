FROM python:3.12-slim

ARG TARGETARCH

RUN <<EOF
set -eux
apt-get update
apt-get install -y --no-install-recommends curl ca-certificates xz-utils
case "${TARGETARCH}" in
    amd64) FFMPEG_ARCH="linux64" ;;
    arm64) FFMPEG_ARCH="linuxarm64" ;;
    *) echo "Unsupported architecture: ${TARGETARCH}" && exit 1 ;;
esac
curl -L "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-${FFMPEG_ARCH}-gpl.tar.xz" \
    | tar xJ -C /usr/local --strip-components=1 --wildcards "ffmpeg-master-latest-${FFMPEG_ARCH}-gpl/bin/ffmpeg"
apt-get purge -y curl xz-utils
apt-get autoremove -y
rm -rf /var/lib/apt/lists/*
EOF

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
COPY README.md ./
COPY .env.example ./

RUN uv sync --frozen --no-dev

EXPOSE 10201

ENV PYTHONUNBUFFERED=1 \
    SERVER__HOST=0.0.0.0 \
    SERVER__PORT=10201

ENTRYPOINT ["uv", "run", "--no-sync", "aivis-openai-tts-bridge", "serve"]
