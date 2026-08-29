"""Shared tag storage for BetterIt.

A "tag" is a named preset (e.g. "Chat", "LinkedIn Post") mapped to a prompt
that steers how the LLM rewrites the user's text. Tags are persisted to a
small JSON file living next to the app so both the floating window and the
settings window can read/write the same data.
"""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_TAGS: dict[str, str] = {
    "Chat": (
        "Improve grammar, spelling, and clarity while keeping a casual, "
        "friendly tone suitable for a chat message. Keep it short."
    ),
    "LinkedIn Post": (
        "Rewrite this as a polished, professional LinkedIn post. Keep it "
        "concise, engaging, and appropriate for a professional network audience."
    ),
    "Email": (
        "Rewrite this as a clear, polite, and professional email while "
        "preserving the original intent and any specific details."
    ),
    "Twitter/X Post": (
        "Rewrite this as a punchy, concise post suitable for Twitter/X. "
        "Keep the core message but make it snappy and casual."
    ),
}


class TagStore:
    """Loads/saves user-defined tags (name -> prompt) to `tags.json`,
    seeded with a few useful defaults on first run."""

    def __init__(self) -> None:
        self._path = Path(__file__).resolve().parent / "tags.json"
        self._tags: dict[str, str] = {}
        self.load()

    def load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data:
                    self._tags = {str(k): str(v) for k, v in data.items()}
                    return
            except (json.JSONDecodeError, OSError):
                pass
        # Fall back to (and persist) the defaults.
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
