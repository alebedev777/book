"""Langfuse: локальный или cloud — трассы генерации книги."""
from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from langfuse import get_client, propagate_attributes

from app.config import get_settings

P = ParamSpec("P")
R = TypeVar("R")

__all__ = [
    "configure_langfuse",
    "flush_langfuse",
    "observe",
    "order_trace",
]


def configure_langfuse() -> bool:
    """Прокидывает ключи из Settings в env (читает SDK)."""
    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
        os.environ.pop("LANGFUSE_SECRET_KEY", None)
        return False
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
    os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
    if settings.langfuse_base_url:
        base = settings.langfuse_base_url.rstrip("/")
        os.environ["LANGFUSE_BASE_URL"] = base
        os.environ["LANGFUSE_HOST"] = base
    return True


def flush_langfuse() -> None:
    if not configure_langfuse():
        return
    try:
        get_client().flush()
    except Exception:
        pass


def observe(
    func: Callable[P, R] | None = None,
    *,
    name: str | None = None,
    **kwargs: Any,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """Langfuse @observe, если ключи заданы; иначе no-op."""
    def wrap(f: Callable[P, R]) -> Callable[P, R]:
        if not configure_langfuse():
            return f
        from langfuse import observe as lf_observe

        decorated = lf_observe(name=name, **kwargs)(f)
        return decorated  # type: ignore[return-value]

    if func is not None:
        return wrap(func)
    return wrap


class order_trace:
    """session_id = order_id, метаданные заказа на трассе."""

    def __init__(
        self,
        order_id: str,
        *,
        telegram_user_id: int | None = None,
        theme_id: str | None = None,
        style_id: str | None = None,
        child_name: str | None = None,
    ) -> None:
        self._order_id = order_id
        self._meta = {
            k: v
            for k, v in {
                "theme_id": theme_id,
                "style_id": style_id,
                "child_name": child_name,
            }.items()
            if v
        }
        self._user_id = str(telegram_user_id) if telegram_user_id else None
        self._cm = None

    def __enter__(self):
        if not configure_langfuse():
            return self
        self._cm = propagate_attributes(
            user_id=self._user_id,
            session_id=self._order_id,
            metadata=self._meta or None,
            tags=["book"],
        )
        self._cm.__enter__()
        return self

    def __exit__(self, *exc):
        if self._cm is not None:
            return self._cm.__exit__(*exc)
        return None