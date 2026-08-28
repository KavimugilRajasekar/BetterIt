"""Thin wrapper around the OpenRouter chat completions API for grammar correction."""
from __future__ import annotations

import os
import re

import requests

from .prompts import GRAMMAR_SYSTEM

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _strip_wrappers(text: str) -> str:
    """Remove code-fence wrappers and leading/trailing quotes the model may add."""
    text = text.strip()
    # Strip ``` blocks the model occasionally wraps answers in
    fenced = re.match(r"^```(?:\w+)?\n?(.*?)\n?```$", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    # Strip a single pair of wrapping quotes
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        text = text[1:-1].strip()
    return text


class GrammarError(RuntimeError):
    """Raised when the LLM call fails or returns something unusable."""


def correct_grammar(text: str, *, model: str | None = None) -> str:
    """Send `text` to OpenRouter and return the grammar-corrected version.

    Raises GrammarError on API failure or empty response.
    """
    text = (text or "").strip()
    if not text:
        raise GrammarError("No text to correct.")

    api_key = os.environ.get("OPEN_ROUTER")
    if not api_key:
        raise GrammarError("OPEN_ROUTER is not set. Edit your .env file.")

    model = model or os.environ.get("MODEL", "openai/gpt-4o-mini")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": GRAMMAR_SYSTEM},
            {"role": "user", "content": text},
        ],
        "temperature": 0.2,
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
    except requests.exceptions.Timeout:
        raise GrammarError("Request to OpenRouter timed out.")
    except requests.exceptions.RequestException as exc:
        raise GrammarError(f"Network error: {exc}") from exc

    if response.status_code != 200:
        raise GrammarError(
            f"OpenRouter returned HTTP {response.status_code}: {response.text}"
        )

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        raise GrammarError(f"Unexpected response format: {exc}") from exc

    if content is None:
        raise GrammarError("OpenRouter returned an empty message.")

    cleaned = _strip_wrappers(content)
    if not cleaned:
        raise GrammarError("OpenRouter returned an empty result after cleaning.")

    return cleaned
