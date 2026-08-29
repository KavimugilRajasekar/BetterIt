"""Shared tag and configuration storage for BetterIt.

A "tag" is a named preset (e.g. "Grammar & Flow", "Professional Email", "LinkedIn Post")
mapped to a prompt that steers how the LLM rewrites the user's text.
Settings and tags are persisted to small JSON files in the user app directory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_TAGS: dict[str, str] = {
    "Grammar & Clarity": (
        "Fix all grammar, spelling, punctuation, and phrasing errors. "
        "Make the text flow smoothly, clearly, and naturally while strictly preserving its original meaning and tone."
    ),
    "Professional Email": (
        "Rewrite this into a clear, polite, and professional email with a natural greeting and closing if appropriate. "
        "Ensure the message is structured, courteous, and easy to read."
    ),
    "LinkedIn Post": (
        "Rewrite this as an engaging, high-impact LinkedIn post. "
        "Use strong hooks, clean line breaks for readability, professional yet conversational phrasing, and 2-3 relevant hashtags."
    ),
    "Twitter / X": (
        "Rewrite this as a punchy, engaging post suitable for Twitter/X. "
        "Keep it concise, energetic, and under 280 characters with maximum clarity."
    ),
    "Chat / Casual": (
        "Improve grammar, spelling, and flow while keeping a warm, friendly, and casual conversational tone suitable for direct messaging or Slack."
    ),
    "Make Concise": (
        "Condense and tighten this text. Remove fluff, redundancies, and filler words while preserving all essential points and core message."
    ),
    "Bullet Points": (
        "Organize the key information and ideas in this text into a clean, well-formatted bulleted list with clear, easy-to-read takeaways."
    ),
}

DEFAULT_CONFIG: dict[str, Any] = {
    "default_tag": "Grammar & Clarity",
    "model": "openai/gpt-4o-mini",
    "always_on_top": True,
}


class TagStore:
    """Loads/saves user-defined tags and general app settings."""

    def __init__(self) -> None:
        self._dir = Path(__file__).resolve().parent
        self._path = self._dir / "tags.json"
        self._config_path = self._dir / "config.json"
        self._tags: dict[str, str] = {}
        self._config: dict[str, Any] = {}
        self.load()
        self.load_config()

    # -- Tag management ----------------------------------------------------

    def load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data:
                    self._tags = {str(k): str(v) for k, v in data.items()}
                    return
            except (json.JSONDecodeError, OSError):
                pass
        # Fall back to defaults
        self._tags = dict(DEFAULT_TAGS)
        self.save()

    def save(self) -> None:
        try:
            self._path.write_text(
                json.dumps(self._tags, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass

    def names(self) -> list[str]:
        return sorted(self._tags.keys(), key=str.lower)

    def prompt_for(self, name: str) -> str:
        return self._tags.get(name, "")

    def set_tag(self, name: str, prompt: str) -> None:
        self._tags[name] = prompt
        self.save()

    def rename(self, old_name: str, new_name: str, prompt: str) -> None:
        if old_name in self._tags and old_name != new_name:
            del self._tags[old_name]
        self._tags[new_name] = prompt
        self.save()

    def delete(self, name: str) -> bool:
        """Returns False (and refuses) if this would remove the last tag."""
        if len(self._tags) <= 1 or name not in self._tags:
            return False
        del self._tags[name]
        self.save()
        return True

    def reset_to_defaults(self) -> None:
        self._tags = dict(DEFAULT_TAGS)
        self.save()

    # -- Config management -------------------------------------------------

    def load_config(self) -> None:
        self._config = dict(DEFAULT_CONFIG)
        if self._config_path.exists():
            try:
                data = json.loads(self._config_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._config.update(data)
            except (json.JSONDecodeError, OSError):
                pass
        else:
            self.save_config()

    def save_config(self) -> None:
        try:
            self._config_path.write_text(
                json.dumps(self._config, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass

    def get_config(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        self._config[key] = value
        self.save_config()
