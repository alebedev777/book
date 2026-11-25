#!/usr/bin/env python3
"""Публикует локальные промпты в Langfuse с меткой production."""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.observability import configure_langfuse  # noqa: E402
from app.prompts import STORY_PROMPT_NAME, story_fallback_messages  # noqa: E402


def main() -> None:
    if not configure_langfuse():
        sys.exit("Нужны LANGFUSE_PUBLIC_KEY и LANGFUSE_SECRET_KEY")

    from langfuse import get_client

    messages = story_fallback_messages()
    prompt = get_client().create_prompt(
        name=STORY_PROMPT_NAME,
        type="chat",
        prompt=messages,
        labels=["production"],
        tags=["book", "story"],
        commit_message="Richer read-aloud pages; lesson shown in action, not spoken",
    )
    print(f"{prompt.name} v{prompt.version} labels={prompt.labels}")


if __name__ == "__main__":
    main()