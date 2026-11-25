import uuid
from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.bot_notify import send_book_to_user_sync
from app.catalog import get_style_illustration_brief, get_theme_learning_goal, get_theme_title
from app.config import get_settings
from app.image_generator import (
    describe_child_from_photo,
    generate_cover_image,
    generate_hero_reference,
    generate_page_image,
)
from app.models import Order, OrderStatus
from app.pdf_builder import build_pdf
from app.schemas import StoryBook
from app.storage import delete_object, download_bytes, upload_bytes
from app.story_generator import generate_story
from app.observability import flush_langfuse, observe, order_trace
from app.worker.celery_app import celery_app

settings = get_settings()
sync_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
SyncSession = sessionmaker(sync_engine, expire_on_commit=False)


def _resolve_learning_goal(order: Order) -> str:
    if order.theme_id:
        goal = get_theme_learning_goal(order.theme_id)
        if goal:
            return goal
    if order.custom_theme:
        return order.custom_theme
    return "Доброта и забота о других."


def _set_progress(session: Session, order: Order, status: OrderStatus, percent: int) -> None:
    order.status = status
    order.progress_percent = percent
    session.commit()


@observe(name="generate_book")
def _generate_book_pipeline(self, order: Order, session: Session) -> None:
    page_count = settings.mvp_pages
    learning_goal = _resolve_learning_goal(order)
    style_prompt = get_style_illustration_brief(order.style_id) or ""
    theme_title = get_theme_title(order.theme_id)

    try:
        _set_progress(session, order, OrderStatus.generating_text, 10)

        photo: bytes | None = None
        if not settings.openai_api_key:
            book = _demo_story(order.child_name, page_count)
            character_bible = "A cheerful child with short brown hair, rosy cheeks, yellow sweater."
        else:
            book = generate_story(
                child_name=order.child_name,
                child_age=order.child_age,
                learning_goal=learning_goal,
                theme_id=order.theme_id,
                page_count=page_count,
            )
            photo = download_bytes(order.photo_key)
            character_bible = describe_child_from_photo(photo, child_age=order.child_age)

        order.story_json = book.model_dump()
        order.character_bible = character_bible
        session.commit()

        _set_progress(session, order, OrderStatus.generating_images, 35)
        page_images: list[bytes] = []
        cover_bytes: bytes | None = None
        prefix = f"orders/{order.id}"

        if settings.openai_api_key:
            if photo is None:
                raise RuntimeError("photo_required")
            hero_bytes = generate_hero_reference(
                style_prompt=style_prompt,
                character_bible=character_bible,
                photo_reference=photo,
                child_age=order.child_age,
            )
            upload_bytes(hero_bytes, f"{prefix}/hero_reference.jpg", "image/jpeg")
            order.progress_percent = 42
            session.commit()

            cover_bytes = generate_cover_image(
                style_prompt=style_prompt,
                title=book.title,
                hero_name=book.hero_name,
                hero_reference=hero_bytes,
                child_age=order.child_age,
                theme_title=theme_title,
                scene=book.pages[0].illustration_scene if book.pages else "",
            )
            upload_bytes(cover_bytes, f"{prefix}/cover.jpg", "image/jpeg")
            order.progress_percent = 48
            session.commit()
        else:
            hero_bytes = _demo_image(0)

        for i, page in enumerate(book.pages):
            if settings.openai_api_key:
                img = generate_page_image(
                    style_prompt=style_prompt,
                    illustration_scene=page.illustration_scene,
                    page_text=page.text,
                    hero_reference=hero_bytes,
                    child_age=order.child_age,
                    theme_title=theme_title,
                )
            else:
                img = _demo_image(page.page)
            key = f"{prefix}/pages/{page.page:02d}.jpg"
            upload_bytes(img, key, "image/jpeg")
            page_images.append(img)
            pct = 48 + int(38 * (i + 1) / len(book.pages))
            order.progress_percent = pct
            session.commit()

        if not settings.openai_api_key:
            cover_bytes = page_images[0] if page_images else _demo_image(0)

        _set_progress(session, order, OrderStatus.building_pdf, 88)
        pdf_bytes = build_pdf(book=book, page_images=page_images, cover_image=cover_bytes)
        pdf_key = f"{prefix}/book.pdf"
        upload_bytes(pdf_bytes, pdf_key, "application/pdf")

        preview_keys = [f"{prefix}/pages/{book.pages[i].page:02d}.jpg" for i in range(min(4, len(book.pages)))]
        order.pdf_key = pdf_key
        order.preview_keys = preview_keys
        order.page_count = len(book.pages)
        order.status = OrderStatus.done
        order.progress_percent = 100
        order.error_code = None
        order.error_message = None
        session.commit()

        send_book_to_user_sync(
            telegram_user_id=order.telegram_user_id,
            pdf_bytes=pdf_bytes,
            title=book.title,
            preview_images=page_images[:4],
        )
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            order.status = OrderStatus.failed
            order.error_code = "generation_failed"
            order.error_message = "Не удалось создать книгу. Попробуйте позже."
            order.progress_percent = 0
            session.commit()
            return
        raise self.retry(exc=exc, countdown=30) from exc


@celery_app.task(name="app.worker.tasks.generate_book_task", bind=True, max_retries=2)
def generate_book_task(self, order_id: str) -> None:
    try:
        oid = uuid.UUID(order_id)
        with SyncSession() as session:
            order = session.get(Order, oid)
            if not order:
                return
            if order.status == OrderStatus.done:
                return
            with order_trace(
                order_id,
                telegram_user_id=order.telegram_user_id,
                theme_id=order.theme_id,
                style_id=order.style_id,
                child_name=order.child_name,
            ):
                _generate_book_pipeline(self, order, session)
    finally:
        flush_langfuse()


@celery_app.task(name="app.worker.tasks.cleanup_expired_photos")
def cleanup_expired_photos() -> int:
    now = datetime.now(UTC)
    removed = 0
    with SyncSession() as session:
        rows = session.execute(
            select(Order).where(Order.expires_at.is_not(None), Order.expires_at < now, Order.photo_key.is_not(None))
        ).scalars()
        for order in rows:
            try:
                delete_object(order.photo_key)
                order.photo_key = None
                removed += 1
            except Exception:
                continue
        session.commit()
    return removed


def _demo_story(child_name: str, page_count: int) -> StoryBook:
    from app.schemas import StoryPage

    hero = child_name[:1].upper() + "ушка" if child_name else "Герой"
    pages = [
        StoryPage(
            page=i + 1,
            text=f"Жил-был {hero}. В этот день он учился важному уроку — шаг за шагом, стр. {i + 1}.",
            illustration_scene=f"A child exploring a sunny meadow, page {i + 1}, whimsical storybook scene",
        )
        for i in range(page_count)
    ]
    return StoryBook(title=f"Приключения {hero}", hero_name=hero, pages=pages)


def _demo_image(page: int) -> bytes:
    from PIL import Image, ImageDraw
    import io

    img = Image.new("RGB", (512, 512), color=(240, 248, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((156, 120, 356, 320), fill=(255, 220, 180))
    draw.text((200, 400), f"Page {page}", fill=(50, 50, 80))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()