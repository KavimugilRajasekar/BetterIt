"""OpenRouter API client for BetterIt text transformation and rewriting."""
from __future__ import annotations

import os
import re
from typing import Any

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_BASE = (
    "You are BetterIt, an expert AI writing assistant and text transformer. "
    "Your goal is to rewrite and improve the user's text according to their instructions.\n"
    "Guidelines:\n"
    "1. Follow the user's rewrite instructions, style, and tone strictly.\n"
    "2. Preserve essential facts, core meaning, and language from the original text.\n"
    "3. Fix all grammar, spelling, punctuation, and phrasing seamlessly.\n"
    "4. Return ONLY the rewritten text without preambles, introductory commentary, quotes, or code fences."
)


def _strip_wrappers(text: str) -> str:
    """Remove code-fence wrappers and leading/trailing quotes the model may add."""
    text = text.strip()
    # Strip ``` blocks the model occasionally wraps answers in
    fenced = re.match(r"^```(?:\w+)?\n?(.*?)\n?```$", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    # Strip a single pair of wrapping quotes if the whole text is enclosed
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        text = text[1:-1].strip()
    return text


def build_messages(text: str, prompt: str | None = None) -> list[dict[str, str]]:
    """Build the chat completion messages for a rewrite request."""
    if not prompt or not prompt.strip():
        return [
            {
                "role": "system",
                "content": (
                    "You are a grammar and spelling corrector. Fix grammar, spelling, and punctuation. "
                    "Preserve the original meaning, tone, and language. "
                    "Return ONLY the corrected text with no commentary, no quotes, and no code fences."
                ),
            },
            {"role": "user", "content": text},
        ]

    user_content = (
        f"Instruction / Tag Prompt:\n{prompt.strip()}\n\n"
        f"Original text to rewrite:\n{text}"
    )

    return [
        {"role": "system", "content": SYSTEM_BASE},
        {"role": "user", "content": user_content},
    ]


class GrammarError(RuntimeError):
    """Raised when the LLM call fails or returns something unusable."""


def transform_text(
    text: str,
    prompt: str | None = None,
    *,
    model: str | None = None,
) -> str:
    """Send `text` and optional transformation `prompt` to OpenRouter and return the rewritten version.

    Raises GrammarError on API failure or empty response.
    """
    text = (text or "").strip()
    if not text:
        raise GrammarError("No text provided to transform.")

    api_key = os.environ.get("OPEN_ROUTER")
    if not api_key:
        raise GrammarError("OPEN_ROUTER API key is not set. Edit your .env file or settings.")

    model = model or os.environ.get("MODEL", "openai/gpt-4o-mini")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/betterit/aiwriter",
        "X-Title": "BetterIt AI Writer",
    }

    messages = build_messages(text, prompt)

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=35,
        )
    except requests.exceptions.Timeout:
        raise GrammarError("Request to OpenRouter timed out. Please check your network connection.")
    except requests.exceptions.RequestException as exc:
        raise GrammarError(f"Network error: {exc}") from exc

    if response.status_code != 200:
        error_detail = response.text
        try:
            err_json = response.json()
            if "error" in err_json and "message" in err_json["error"]:
                error_detail = err_json["error"]["message"]
        except Exception:
            pass
        raise GrammarError(f"OpenRouter API error (HTTP {response.status_code}): {error_detail}")

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        raise GrammarError(f"Unexpected response format from OpenRouter: {exc}") from exc

    if content is None:
        raise GrammarError("OpenRouter returned an empty message.")

    cleaned = _strip_wrappers(content)
    if not cleaned:
        raise GrammarError("OpenRouter returned an empty result after cleaning.")

    return cleaned


def correct_grammar(text: str, *, model: str | None = None) -> str:
    """Backward-compatible wrapper for grammar correction."""
    return transform_text(text, prompt=None, model=model)
