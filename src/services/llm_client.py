"""
Pluggable LLM backend for the chat feature. LLM_BACKEND env var selects the
implementation; both speak the same minimal chat() interface so
chat_service.py doesn't need to know which one is active.
"""

import json
import os
from typing import Protocol

import requests


class LLMClient(Protocol):
    def chat(self, system: str, user: str) -> str:
        """Send a system + user prompt, return the model's raw text reply."""
        ...


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

    def chat(self, system: str, user: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


class HostedApiClient:
    """OpenAI-compatible chat completions endpoint (opt-in via LLM_BACKEND=hosted_api)."""

    def __init__(self, base_url: str | None = None, model: str | None = None, api_key: str | None = None):
        self.base_url = base_url or os.environ.get("HOSTED_API_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.environ.get("HOSTED_API_MODEL", "gpt-4o-mini")
        self.api_key = api_key or os.environ.get("HOSTED_API_KEY", "")

    def chat(self, system: str, user: str) -> str:
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def get_llm_client() -> LLMClient:
    backend = os.environ.get("LLM_BACKEND", "ollama")
    if backend == "hosted_api":
        return HostedApiClient()
    return OllamaClient()


def extract_json(text: str) -> dict | None:
    """Best-effort JSON extraction from a model reply that may include
    surrounding prose or markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
