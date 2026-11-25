import base64

import httpx

from app.catalog import load_cover_image_prompt, load_page_image_prompt
from app.config import get_settings
from app.observability import observe
from app.openai_client import get_openai_client

_PAGE_TEXT_PROMPT_LIMIT = 480


def _photo_data_url(photo_bytes: bytes, mime: str = "image/jpeg") -> str:
    b64 = base64.standard_b64encode(photo_bytes).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _input_references(references: list[bytes]) -> list[dict]:
    return [
        {"type": "image_url", "image_url": {"url": _photo_data_url(ref)}}
        for ref in references
    ]


def _text_for_image_prompt(text: str, *, limit: int = _PAGE_TEXT_PROMPT_LIMIT) -> str:
    stripped = (text or "").strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 1].rstrip() + "…"


def _fill_prompt(template: str, **parts: str) -> str:
    filled = template
    for key, value in parts.items():
        filled = filled.replace("{{" + key + "}}", value)
    return filled


def _decode_image_item(item) -> bytes:
    if isinstance(item, dict):
        if item.get("b64_json"):
            return base64.standard_b64decode(item["b64_json"])
        if item.get("url"):
            r = httpx.get(item["url"], timeout=120)
            r.raise_for_status()
            return r.content
    else:
        if item.b64_json:
            return base64.standard_b64decode(item.b64_json)
        if item.url:
            r = httpx.get(item.url, timeout=120)
            r.raise_for_status()
            return r.content
    raise RuntimeError("image_empty")


def _request_image(
    prompt: str,
    *,
    references: list[bytes],
    aspect_ratio: str = "1:1",
    size: str = "1024x1024",
) -> bytes:
    settings = get_settings()
    extra: dict = {
        "aspect_ratio": aspect_ratio,
        "output_format": "jpeg",
    }
    if references:
        extra["input_references"] = _input_references(references)

    if settings.openai_base_url:
        url = f"{settings.openai_base_url.rstrip('/')}/images"
        payload: dict = {
            "model": settings.openai_image_model,
            "prompt": prompt,
            "n": 1,
            **extra,
        }
        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=180.0,
        )
        response.raise_for_status()
        data = response.json()
        if err := data.get("error"):
            msg = err.get("message") if isinstance(err, dict) else str(err)
            raise RuntimeError(msg or "image_api_error")
        items = data.get("data") or []
        if not items:
            raise RuntimeError("image_empty")
        return _decode_image_item(items[0])

    client = get_openai_client()
    result = client.images.generate(
        model=settings.openai_image_model,
        prompt=prompt,
        size=size,
        quality="medium",
        extra_body=extra if extra else None,
    )
    if not result.data:
        raise RuntimeError("image_empty")
    return _decode_image_item(result.data[0])


@observe(name="character_vision")
def describe_child_from_photo(
    photo_bytes: bytes,
    mime: str = "image/jpeg",
    *,
    child_age: int | None = None,
) -> str:
    settings = get_settings()
    client = get_openai_client()
    vision_model = settings.openai_vision_model or settings.openai_chat_model
    data_url = _photo_data_url(photo_bytes, mime)
    age = child_age if child_age else 5
    response = client.chat.completions.create(
        model=vision_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Reference photo for the main hero of a children's storybook. "
                            f"The hero in the book is a child of {age} years old, even if the photo shows an adult. "
                            "Write a character bible for illustrators: hair (color, length, texture), "
                            "face shape, eyebrows, eyes, skin tone, nose, ears, "
                            "clothing colors in the photo, and any distinctive features to keep. "
                            f"State that the drawn hero is {age} years old with preschool proportions "
                            "if under 7: large head, short body, round cheeks, small hands. "
                            "Do not describe a teenager or an adult body. Omit facial hair. "
                            "Do not use personal names. One dense paragraph in English."
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        max_tokens=400,
    )
    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("vision_empty")
    return text


@observe(name="hero_reference")
def generate_hero_reference(
    *,
    style_prompt: str,
    character_bible: str,
    photo_reference: bytes,
    child_age: int | None = None,
    size: str = "1024x1024",
) -> bytes:
    age = child_age if child_age else 5
    prompt = (
        f"{style_prompt}. "
        "Children's storybook main character reference sheet: three-quarter bust, "
        "clear face and outfit, soft simple background, no scene action. "
        "Gentle off-camera gaze — not a selfie, not looking into the lens. "
        f"MANDATORY AGE: draw a child who is {age} years old. "
        "If under 7: preschool proportions, large head, short body, round cheeks, small hands. "
        "Not a teenager, not an adult. "
        f"Character: {character_bible or 'a friendly child hero'}. "
        "Match hair, eyes, skin tone, and clothes from the reference photo. "
        "No text, no watermark, wholesome, child-safe."
    )
    return _request_image(prompt, references=[photo_reference], size=size)


@observe(name="cover_image")
def generate_cover_image(
    *,
    style_prompt: str,
    title: str,
    hero_name: str,
    hero_reference: bytes,
    child_age: int | None = None,
    theme_title: str = "",
    scene: str = "",
    size: str = "1024x1024",
) -> bytes:
    age = child_age if child_age else 5
    prompt = _fill_prompt(
        load_cover_image_prompt(),
        style=style_prompt,
        title=_text_for_image_prompt(title, limit=120),
        hero=_text_for_image_prompt(hero_name, limit=80),
        age=str(age),
        theme=theme_title or "the story theme",
        scene=(scene or "the hero in the world of the story").strip(),
    )
    return _request_image(
        prompt,
        references=[hero_reference],
        aspect_ratio="3:4",
        size=size,
    )


@observe(name="page_image")
def generate_page_image(
    *,
    style_prompt: str,
    illustration_scene: str,
    page_text: str,
    hero_reference: bytes,
    child_age: int | None = None,
    theme_title: str = "",
    size: str = "1024x1024",
) -> bytes:
    age = child_age if child_age else 5
    prompt = _fill_prompt(
        load_page_image_prompt(),
        style=style_prompt,
        scene=(illustration_scene or "").strip(),
        text=_text_for_image_prompt(page_text),
        age=str(age),
        theme=theme_title or "the story theme",
    )
    return _request_image(prompt, references=[hero_reference], size=size)