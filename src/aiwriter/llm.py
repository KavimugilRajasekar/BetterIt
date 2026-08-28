"""Thin wrapper around the OpenAI chat completions API for grammar correction."""
from __future__ import annotations

import os
import re

from openai import OpenAI

from .prompts import GRAMMAR_SYSTEM


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


def correct_grammar(text: str, *, client: OpenAI | None = None, model: str | None = None) -> str:
    """Send `text` to the LLM and return the grammar-corrected version.

    Raises GrammarError on API failure or empty response.
    """
    text = (text or "").strip()
    if not text:
        raise GrammarError("No text to correct.")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise GrammarError("OPENAI_API_KEY is not set. Edit your .env file.")

    client = client or OpenAI()
    model = model or os.environ.get("MODEL", "gpt-4o-mini")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": GRAMMAR_SYSTEM},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
        )
    except Exception as exc:  # openai raises a variety of exception types
        raise GrammarError(f"OpenAI request failed: {exc}") from exc

    if not response.choices:
        raise GrammarError("OpenAI returned no choices.")

    content = response.choices[0].message.content
    if content is None:
        raise GrammarError("OpenAI returned an empty message.")

    cleaned = _strip_wrappers(content)
    if not cleaned:
        raise GrammarError("OpenAI returned an empty result after cleaning.")

    return cleaned
