import json
from functools import lru_cache

from app.config import get_settings
from app.schemas import StyleOut, ThemeOut


@lru_cache
def load_themes() -> list[ThemeOut]:
    settings = get_settings()
    raw = json.loads((settings.shared_dir / "themes.json").read_text(encoding="utf-8"))
    return [ThemeOut.model_validate(x) for x in raw]


@lru_cache
def load_styles() -> list[StyleOut]:
    settings = get_settings()
    raw = json.loads((settings.shared_dir / "styles.json").read_text(encoding="utf-8"))
    return [StyleOut.model_validate({"id": x["id"], "title_ru": x["title_ru"]}) for x in raw]


def get_theme_title(theme_id: str | None) -> str:
    if not theme_id:
        return ""
    theme = get_theme_by_id(theme_id)
    return theme.title_ru if theme else theme_id


def get_theme_learning_goal(theme_id: str) -> str | None:
    for t in load_themes():
        if t.id == theme_id:
            return t.learning_goal
    return None


def get_theme_by_id(theme_id: str) -> ThemeOut | None:
    for t in load_themes():
        if t.id == theme_id:
            return t
    return None


def format_theme_story_brief(theme_id: str) -> str | None:
    theme = get_theme_by_id(theme_id)
    if not theme:
        return None
    beats = "\n".join(f"  - {b}" for b in theme.story_beats)
    return (
        f"Тема: {theme.title_ru}\n"
        f"Цель (для автора, не произносить в сказке): {theme.learning_goal}\n"
        f"Опора (не называть вслух): {theme.archetype}\n"
        f"Скрытый механизм (только структура, не цитата): {theme.jungian_mechanism}\n"
        f"Биты — позвоночник одной истории, не план «один бит = одна страница»:\n{beats}"
    )


def get_style_prompt(style_id: str) -> str | None:
    settings = get_settings()
    raw = json.loads((settings.shared_dir / "styles.json").read_text(encoding="utf-8"))
    for s in raw:
        if s["id"] == style_id:
            return s["style_prompt"]
    return None


def get_style_illustration_brief(style_id: str) -> str | None:
    prompt = get_style_prompt(style_id)
    if not prompt:
        return None
    for s in load_styles():
        if s.id == style_id:
            return f"Style «{s.title_ru}». {prompt}"
    return prompt


def load_page_image_prompt() -> str:
    return _load_prompt("image_page.md")


def load_cover_image_prompt() -> str:
    return _load_prompt("image_cover.md")


def _load_prompt(name: str) -> str:
    settings = get_settings()
    return (settings.shared_dir / "prompts" / name).read_text(encoding="utf-8")