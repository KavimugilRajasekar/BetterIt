"""Shared tag and configuration storage for BetterIt.

A "tag" is a named preset (e.g. "Grammar & Clarity", "Professional Email", "LinkedIn Post")
mapped to a prompt that steers how the LLM rewrites the user's text.
Settings, key spaces, models, and tags are persisted to small JSON files in the user app directory.
"""

from __future__ import annotations

import json
import os
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

DEFAULT_MODELS: list[str] = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-haiku",
    "google/gemini-2.5-flash",
    "deepseek/deepseek-chat",
    "meta-llama/llama-3.3-70b-instruct",
]

DEFAULT_KEY_SPACES: list[dict[str, Any]] = [
    {
        "name": "OpenRouter",
        "api_key": "",
        "models": list(DEFAULT_MODELS),
        "selected_model": "openai/gpt-4o-mini",
    }
]

DEFAULT_CONFIG: dict[str, Any] = {
    "default_tag": "Grammar & Clarity",
    "always_on_top": True,
    "active_key_space": "OpenRouter",
    "key_spaces": DEFAULT_KEY_SPACES,
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

    # -- Config & Key Spaces management ------------------------------------

    def load_config(self) -> None:
        self._config = dict(DEFAULT_CONFIG)
        if self._config_path.exists():
            try:
                data = json.loads(self._config_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._config.update(data)
            except (json.JSONDecodeError, OSError):
                pass
        
        # Ensure key_spaces is properly populated
        spaces = self._config.get("key_spaces")
        if not isinstance(spaces, list) or not spaces:
            # Seed from existing single model or .env if available
            initial_key = os.environ.get("OPEN_ROUTER", "")
            initial_model = self._config.get("model") or os.environ.get("MODEL", "openai/gpt-4o-mini")
            models_list = list(DEFAULT_MODELS)
            if initial_model and initial_model not in models_list:
                models_list.insert(0, initial_model)
            
            self._config["key_spaces"] = [
                {
                    "name": "Default Space",
                    "api_key": initial_key,
                    "models": models_list,
                    "selected_model": initial_model,
                }
            ]
            self._config["active_key_space"] = "Default Space"
        
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

    # -- Key Space Specific Operations -------------------------------------

    def get_key_spaces(self) -> list[dict[str, Any]]:
        spaces = self._config.get("key_spaces", [])
        if not isinstance(spaces, list):
            return []
        return spaces

    def get_key_space_names(self) -> list[str]:
        return [str(s.get("name", "Unnamed Space")) for s in self.get_key_spaces()]

    def get_active_key_space_name(self) -> str:
        active = self._config.get("active_key_space")
        names = self.get_key_space_names()
        if active in names:
            return str(active)
        if names:
            self.set_active_key_space_name(names[0])
            return names[0]
        return "Default Space"

    def set_active_key_space_name(self, name: str) -> None:
        self._config["active_key_space"] = name
        self.save_config()

    def get_key_space(self, name: str) -> dict[str, Any] | None:
        for space in self.get_key_spaces():
            if space.get("name") == name:
                return space
        return None

    def get_active_key_space(self) -> dict[str, Any]:
        active_name = self.get_active_key_space_name()
        space = self.get_key_space(active_name)
        if space is not None:
            return space
        spaces = self.get_key_spaces()
        if spaces:
            return spaces[0]
        # Fallback if empty
        default_space = {
            "name": "Default Space",
            "api_key": "",
            "models": list(DEFAULT_MODELS),
            "selected_model": "openai/gpt-4o-mini",
        }
        self._config["key_spaces"] = [default_space]
        self._config["active_key_space"] = "Default Space"
        self.save_config()
        return default_space

    def add_key_space(
        self,
        name: str,
        api_key: str = "",
        models: list[str] | None = None,
        selected_model: str = "",
    ) -> bool:
        name = name.strip()
        if not name:
            return False
        if any(s.get("name", "").lower() == name.lower() for s in self.get_key_spaces()):
            return False
        
        models_list = list(models) if models else list(DEFAULT_MODELS)
        sel_model = selected_model if selected_model in models_list else (models_list[0] if models_list else "openai/gpt-4o-mini")
        
        new_space = {
            "name": name,
            "api_key": api_key.strip(),
            "models": models_list,
            "selected_model": sel_model,
        }
        self.get_key_spaces().append(new_space)
        self.set_active_key_space_name(name)
        self.save_config()
        return True

    def delete_key_space(self, name: str) -> bool:
        spaces = self.get_key_spaces()
        if len(spaces) <= 1:
            return False  # Keep at least one space
        
        idx = next((i for i, s in enumerate(spaces) if s.get("name") == name), -1)
        if idx == -1:
            return False
        
        del spaces[idx]
        if self._config.get("active_key_space") == name:
            self._config["active_key_space"] = spaces[0].get("name", "Default Space")
        self.save_config()
        return True

    def update_key_space(
        self,
        space_name: str,
        *,
        api_key: str | None = None,
        models: list[str] | None = None,
        selected_model: str | None = None,
    ) -> bool:
        space = self.get_key_space(space_name)
        if not space:
            return False
        
        if api_key is not None:
            space["api_key"] = api_key.strip()
        if models is not None:
            space["models"] = [str(m).strip() for m in models if str(m).strip()]
        if selected_model is not None:
            space["selected_model"] = selected_model.strip()
            
        self.save_config()
        return True

    def add_model_to_space(self, space_name: str, model_id: str) -> bool:
        model_id = model_id.strip()
        if not model_id:
            return False
        space = self.get_key_space(space_name)
        if not space:
            return False
        models = space.setdefault("models", [])
        if model_id not in models:
            models.append(model_id)
        space["selected_model"] = model_id
        self.save_config()
        return True

    def delete_model_from_space(self, space_name: str, model_id: str) -> bool:
        space = self.get_key_space(space_name)
        if not space:
            return False
        models = space.get("models", [])
        if len(models) <= 1 or model_id not in models:
            return False
        models.remove(model_id)
        if space.get("selected_model") == model_id:
            space["selected_model"] = models[0]
        self.save_config()
        return True

    def get_active_api_key(self) -> str:
        space = self.get_active_key_space()
        key = str(space.get("api_key", "")).strip()
        if key:
            return key
        # Fallback to env for backward compatibility if configured
        return os.environ.get("OPEN_ROUTER", "").strip()

    def get_active_model(self) -> str:
        space = self.get_active_key_space()
        model = str(space.get("selected_model", "")).strip()
        if model:
            return model
        return "openai/gpt-4o-mini"
