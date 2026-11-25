from app.config import get_settings
from app.observability import configure_langfuse


def get_openai_client():
    settings = get_settings()
    kwargs: dict[str, str] = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url.rstrip("/")
    if configure_langfuse():
        from langfuse.openai import OpenAI

        return OpenAI(**kwargs)
    from openai import OpenAI

    return OpenAI(**kwargs)