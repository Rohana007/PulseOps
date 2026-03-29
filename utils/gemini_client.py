"""Shared Gemini API client for PulseOps (Google GenAI SDK)."""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


@lru_cache(maxsize=1)
def get_genai_client() -> genai.Client:
    key = os.getenv("GEMINI_API_KEY")
    if not key or key == "your_key_here":
        raise RuntimeError(
            "Set GEMINI_API_KEY in .env (see Google AI Studio). "
            "Do not commit real keys."
        )
    return genai.Client(api_key=key)


def generate_text(prompt: str, max_output_tokens: int = 2048) -> str:
    """Run a single-turn text generation and return trimmed text."""
    client = get_genai_client()
    resp = client.models.generate_content(
        model=DEFAULT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=max_output_tokens),
    )
    text = getattr(resp, "text", None) or ""
    return text.strip()
