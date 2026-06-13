import json
import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from pulseiq_backend.core.config import settings

logger = logging.getLogger(__name__)

_GENERATE_URL = f"{settings.ollama_base_url}/api/generate"
_EMBED_URL = f"{settings.ollama_base_url}/api/embed"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
async def _post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


async def generate(prompt: str) -> str:
    """Generate text from Ollama, falls back to llama2 on failure."""
    for model in (settings.ollama_model, settings.ollama_fallback_model):
        try:
            data = await _post(_GENERATE_URL, {"model": model, "prompt": prompt, "stream": False})
            return data["response"]
        except Exception:
            logger.warning("Ollama model %s failed, trying fallback", model)
    raise RuntimeError("All Ollama models failed")


async def embed(text: str) -> list[float]:
    """Generate an embedding vector for the given text."""
    data = await _post(_EMBED_URL, {"model": settings.ollama_model, "input": text})
    return data["embeddings"][0]
