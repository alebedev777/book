"""Промпты генерации: Langfuse (label production), локальные файлы — fallback."""
from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.observability import configure_langfuse

STORY_PROMPT_NAME = "story"


def _fill(template: str, **kwargs: object) -> str:
    out = template
    for key, value in kwargs.items():
        out = out.replace("{{" + key + "}}", "" if value is None else str(value))
    return out


def story_fallback_messages() -> list[dict[str, str]]:
    settings = get_settings()
    prompts = settings.shared_dir / "prompts"
    return [
        {"role": "system", "content": (prompts / "story_system.md").read_text(encoding="utf-8")},
        {"role": "user", "content": (prompts / "story_user.md").read_text(encoding="utf-8")},
    ]


def compile_story_messages(**kwargs: object) -> tuple[list[dict[str, str]], Any | None]:
    """Сообщения chat-промпта story и клиент Langfuse для привязки к generation."""
    fallback = story_fallback_messages()
    if not configure_langfuse():
        return [_compile_message(m, kwargs) for m in fallback], None

    from langfuse import get_client

    prompt = get_client().get_prompt(
        STORY_PROMPT_NAME,
        type="chat",
        label="production",
        fallback=fallback,
    )
    messages = [
        {"role": str(m["role"]), "content": str(m["content"])}
        for m in prompt.compile(**kwargs)
    ]
    linked = None if getattr(prompt, "is_fallback", False) else prompt
    return messages, linked


def _compile_message(message: dict[str, str], kwargs: dict[str, object]) -> dict[str, str]:
    return {"role": message["role"], "content": _fill(message["content"], **kwargs)}
