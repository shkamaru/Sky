"""
LLM wrapper — single model active at a time via Ollama.
Designed with a BaseLLMProvider interface for future multi-model routing.
Uses AsyncClient throughout so the FastAPI event loop is never blocked.
"""
import ollama
from ollama import AsyncClient
from typing import AsyncGenerator


DEFAULT_MODEL = "qwen2.5:14b"
EMBED_MODEL = "nomic-embed-text"

# One shared async client
_async_client = AsyncClient()


class BaseLLMProvider:
    async def chat_stream(self, messages: list[dict], model: str) -> AsyncGenerator[str, None]:
        raise NotImplementedError

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    def list_models(self) -> list[str]:
        raise NotImplementedError


class OllamaProvider(BaseLLMProvider):

    async def chat_stream(
        self,
        messages: list[dict],
        model: str = DEFAULT_MODEL,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama without blocking the event loop."""
        response = await _async_client.chat(
            model=model,
            messages=messages,
            stream=True,
        )
        async for chunk in response:
            token = chunk.message.content
            if token:
                yield token

    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector via nomic-embed-text."""
        response = await _async_client.embeddings(model=EMBED_MODEL, prompt=text)
        return response.embedding

    def list_models(self) -> list[str]:
        """Return locally available Ollama models (sync, called rarely)."""
        response = ollama.list()
        return [m.model for m in response.models]


# Singleton — import this everywhere
llm = OllamaProvider()
