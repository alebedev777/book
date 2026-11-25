from app.config import get_settings
from app.observability import observe
from app.openai_client import get_openai_client


@observe(name="moderation")
def moderate_text(text: str) -> None:
    settings = get_settings()
    if not settings.openai_api_key:
        return
    client = get_openai_client()
    result = client.moderations.create(input=text)
    if result.results[0].flagged:
        raise ValueError("theme_rejected")