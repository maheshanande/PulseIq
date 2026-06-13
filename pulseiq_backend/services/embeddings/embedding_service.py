from pulseiq_backend.services.llm import ollama_client


async def embed_text(text: str) -> list[float]:
    return await ollama_client.embed(text)
