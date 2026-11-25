import json

from app.catalog import format_theme_story_brief
from app.config import get_settings
from app.moderation import moderate_text
from app.observability import observe
from app.openai_client import get_openai_client
from app.prompts import compile_story_messages
from app.schemas import StoryBook


def _page_word_range(age: int | None) -> tuple[int, int]:
    if age is None or age <= 6:
        return 28, 45
    if age <= 8:
        return 60, 110
    return 80, 140


@observe(name="story_text")
def generate_story(
    *,
    child_name: str,
    child_age: int | None,
    learning_goal: str,
    theme_id: str | None,
    page_count: int,
) -> StoryBook:
    settings = get_settings()
    age_hint = str(child_age) if child_age else "4–8"
    words_lo, words_hi = _page_word_range(child_age)
    theme_brief = format_theme_story_brief(theme_id) if theme_id else None
    narrative_block = theme_brief or f"Тема для автора (не произносить в сказке): {learning_goal}"
    messages, langfuse_prompt = compile_story_messages(
        page_count=page_count,
        child_name=child_name,
        age_hint=age_hint,
        words_lo=words_lo,
        words_hi=words_hi,
        narrative_block=narrative_block,
    )

    client = get_openai_client()
    request: dict = {
        "model": settings.openai_chat_model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.9,
    }
    # langfuse.openai accepts this; the plain OpenAI client rejects unknown kwargs.
    if langfuse_prompt is not None:
        request["langfuse_prompt"] = langfuse_prompt
    response = client.chat.completions.create(**request)
    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)
    book = StoryBook.model_validate(data)
    if len(book.pages) > page_count:
        book.pages = book.pages[:page_count]
    if settings.moderate_story_text:
        moderate_text("\n".join(p.text for p in book.pages))
    return book