#!/usr/bin/env python3
"""Генерация книги локально: только API, результат в output/. Без БД, Celery, MinIO."""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

# --- тестовые данные по умолчанию ---
DEFAULT_PHOTO = Path("/Users/andrey/Desktop/photo_2026-02-02_14-37-52.jpg")
DEFAULT_CHILD_NAME = "Андрей"
DEFAULT_CHILD_AGE = 5
DEFAULT_THEME_ID = "empathy"  # Сочувствие
DEFAULT_STYLE_ID = "anime"
OUTPUT_DIR = REPO / "output"


def main() -> None:
    parser = argparse.ArgumentParser(description="Сгенерировать книгу в output/")
    parser.add_argument("photo", nargs="?", type=Path, default=DEFAULT_PHOTO)
    parser.add_argument("--name", default=DEFAULT_CHILD_NAME)
    parser.add_argument("--age", type=int, default=DEFAULT_CHILD_AGE)
    parser.add_argument("--theme", default=DEFAULT_THEME_ID)
    parser.add_argument("--style", default=DEFAULT_STYLE_ID)
    parser.add_argument("--pages", type=int, default=None, help="число страниц (по умолчанию MVP_PAGES из .env)")
    args = parser.parse_args()

    if not args.photo.is_file():
        sys.exit(f"Фото не найдено: {args.photo}")

    from app.catalog import get_style_illustration_brief, get_theme_learning_goal, get_theme_title
    from app.config import get_settings
    from app.image_generator import (
        describe_child_from_photo,
        generate_cover_image,
        generate_hero_reference,
        generate_page_image,
    )
    from app.observability import flush_langfuse, observe, order_trace
    from app.pdf_builder import build_pdf
    from app.story_generator import generate_story

    @observe(name="generate_book")
    def _generate_book_local() -> Path:
        print("1/6 Текст сказки…", flush=True)
        book = generate_story(
            child_name=args.name,
            child_age=args.age,
            learning_goal=learning_goal,
            theme_id=args.theme,
            page_count=page_count,
        )
        (out / "story.json").write_text(book.model_dump_json(indent=2), encoding="utf-8")
        print(f"   «{book.title}», {len(book.pages)} стр.", flush=True)

        print("2/6 Описание героя по фото…", flush=True)
        character_bible = describe_child_from_photo(photo_bytes, child_age=args.age)
        (out / "character_bible.txt").write_text(character_bible, encoding="utf-8")

        print("3/6 Референс героя…", flush=True)
        hero_bytes = generate_hero_reference(
            style_prompt=style_prompt,
            character_bible=character_bible,
            photo_reference=photo_bytes,
            child_age=args.age,
        )
        (out / "hero_reference.jpg").write_bytes(hero_bytes)

        print("4/6 Обложка…", flush=True)
        cover_scene = book.pages[0].illustration_scene if book.pages else ""
        cover_bytes = generate_cover_image(
            style_prompt=style_prompt,
            title=book.title,
            hero_name=book.hero_name,
            hero_reference=hero_bytes,
            child_age=args.age,
            theme_title=theme_title,
            scene=cover_scene,
        )
        (out / "cover.jpg").write_bytes(cover_bytes)

        print("5/6 Страницы…", flush=True)
        page_images: list[bytes] = []
        for page in book.pages:
            print(f"   стр. {page.page}/{len(book.pages)}…", flush=True)
            img = generate_page_image(
                style_prompt=style_prompt,
                illustration_scene=page.illustration_scene,
                page_text=page.text,
                hero_reference=hero_bytes,
                child_age=args.age,
                theme_title=theme_title,
            )
            path = pages_dir / f"{page.page:02d}.jpg"
            path.write_bytes(img)
            page_images.append(img)

        print("6/6 PDF…", flush=True)
        pdf_bytes = build_pdf(book=book, page_images=page_images, cover_image=cover_bytes)
        pdf_path = out / "book.pdf"
        pdf_path.write_bytes(pdf_bytes)
        return pdf_path

    settings = get_settings()
    if not settings.openai_api_key:
        sys.exit("Нужен OPENAI_API_KEY в .env")

    page_count = args.pages if args.pages is not None else settings.mvp_pages
    theme_title = get_theme_title(args.theme)
    learning_goal = get_theme_learning_goal(args.theme) or theme_title
    style_prompt = get_style_illustration_brief(args.style) or ""

    run_id = uuid.uuid4()
    out = OUTPUT_DIR / str(run_id)
    out.mkdir(parents=True, exist_ok=True)
    pages_dir = out / "pages"
    pages_dir.mkdir(exist_ok=True)

    photo_bytes = args.photo.read_bytes()
    (out / "photo.jpg").write_bytes(photo_bytes)
    meta = {
        "child_name": args.name,
        "child_age": args.age,
        "theme_id": args.theme,
        "style_id": args.style,
        "photo": str(args.photo),
        "page_count": page_count,
    }
    (out / "run.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        with order_trace(
            str(run_id),
            theme_id=args.theme,
            style_id=args.style,
            child_name=args.name,
        ):
            pdf_path = _generate_book_local()
        print(f"\nГотово: {out}")
        print(f"PDF: {pdf_path}")
    finally:
        flush_langfuse()


if __name__ == "__main__":
    main()