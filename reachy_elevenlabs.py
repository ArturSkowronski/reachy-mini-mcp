from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from typing import Any

import httpx


ELEVENLABS_API_BASE_URL = "https://api.elevenlabs.io/v1"


@dataclass(frozen=True)
class ElevenLabsConfig:
    api_key: str
    voice_id: str
    model_id: str = "eleven_multilingual_v2"
    output_format: str = "wav_44100"


def load_elevenlabs_config(
    *,
    api_key: str | None = None,
    voice_id: str | None = None,
    model_id: str | None = None,
    output_format: str | None = None,
) -> ElevenLabsConfig:
    resolved_api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
    resolved_voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID")

    if not resolved_api_key:
        raise ValueError("Missing ElevenLabs API key: set `ELEVENLABS_API_KEY`.")
    if not resolved_voice_id:
        raise ValueError("Missing ElevenLabs voice id: set `ELEVENLABS_VOICE_ID`.")

    return ElevenLabsConfig(
        api_key=resolved_api_key,
        voice_id=resolved_voice_id,
        model_id=model_id
        or os.getenv("ELEVENLABS_MODEL_ID")
        or "eleven_multilingual_v2",
        output_format=output_format
        or os.getenv("ELEVENLABS_OUTPUT_FORMAT")
        or "wav_44100",
    )


async def elevenlabs_tts_bytes(
    *,
    text: str,
    config: ElevenLabsConfig,
    voice_settings: dict[str, Any] | None = None,
    timeout_s: float = 30.0,
) -> bytes:
    if not text.strip():
        raise ValueError("Text must be non-empty.")

    payload: dict[str, Any] = {"text": text, "model_id": config.model_id}
    if voice_settings:
        payload["voice_settings"] = voice_settings

    url = f"{ELEVENLABS_API_BASE_URL}/text-to-speech/{config.voice_id}"

    headers = {
        "xi-api-key": config.api_key,
        "Content-Type": "application/json",
        "Accept": "audio/wav",
    }

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        resp = await client.post(
            url,
            params={"output_format": config.output_format},
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        return resp.content


async def elevenlabs_tts_to_temp_wav(
    *,
    text: str,
    config: ElevenLabsConfig,
    voice_settings: dict[str, Any] | None = None,
    timeout_s: float = 30.0,
) -> str:
    audio_bytes = await elevenlabs_tts_bytes(
        text=text,
        config=config,
        voice_settings=voice_settings,
        timeout_s=timeout_s,
    )

    tmp = tempfile.NamedTemporaryFile(
        prefix="reachy_elevenlabs_", suffix=".wav", delete=False
    )
    try:
        tmp.write(audio_bytes)
        tmp.flush()
        return tmp.name
    finally:
        tmp.close()
