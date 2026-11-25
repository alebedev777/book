import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog import get_theme_learning_goal, load_styles, load_themes
from app.config import get_settings
from app.models import Order, OrderStatus
from app.moderation import moderate_text
from app.schemas import OrderOut
from app.storage import public_url


async def count_active_orders(session: AsyncSession, telegram_user_id: int) -> int:
    active = (
        OrderStatus.pending,
        OrderStatus.generating_text,
        OrderStatus.generating_images,
        OrderStatus.building_pdf,
    )
    result = await session.execute(
        select(func.count())
        .select_from(Order)
        .where(
            and_(
                Order.telegram_user_id == telegram_user_id,
                Order.status.in_(active),
            )
        )
    )
    return int(result.scalar_one())


async def create_order(
    session: AsyncSession,
    *,
    order_id: uuid.UUID,
    telegram_user_id: int,
    theme_id: str | None,
    custom_theme: str | None,
    style_id: str,
    child_name: str,
    child_age: int | None,
    photo_key: str,
) -> Order:
    settings = get_settings()

    if await count_active_orders(session, telegram_user_id) >= settings.rate_limit_active_orders:
        raise ValueError("rate_limit")

    style_ids = {s.id for s in load_styles()}
    if style_id not in style_ids:
        raise ValueError("invalid_style")

    learning_goal = None
    if theme_id:
        learning_goal = get_theme_learning_goal(theme_id)
        if not learning_goal:
            raise ValueError("invalid_theme")
        if custom_theme:
            raise ValueError("theme_conflict")
    elif custom_theme:
        if settings.moderate_custom_themes:
            moderate_text(custom_theme)
        learning_goal = custom_theme.strip()
    else:
        raise ValueError("theme_required")

    order = Order(
        id=order_id,
        telegram_user_id=telegram_user_id,
        theme_id=theme_id,
        custom_theme=custom_theme.strip() if custom_theme else None,
        style_id=style_id,
        child_name=child_name.strip()[:100],
        child_age=child_age,
        photo_key=photo_key,
        prompt_version=settings.prompt_version,
        expires_at=datetime.now(UTC) + timedelta(days=settings.photo_ttl_days),
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_order_for_user(session: AsyncSession, order_id: uuid.UUID, telegram_user_id: int) -> Order | None:
    result = await session.execute(
        select(Order).where(Order.id == order_id, Order.telegram_user_id == telegram_user_id)
    )
    return result.scalar_one_or_none()


def order_to_out(order: Order) -> OrderOut:
    previews = None
    if order.preview_keys:
        previews = [public_url(k) for k in order.preview_keys]
    pdf_url = public_url(order.pdf_key) if order.pdf_key else None
    error_message = order.error_message
    if order.status == OrderStatus.failed and not error_message:
        error_message = "Не удалось создать книгу. Попробуйте позже."
    return OrderOut(
        id=order.id,
        status=order.status,
        progress_percent=order.progress_percent,
        page_count=order.page_count,
        preview_urls=previews,
        pdf_url=pdf_url,
        error_message=error_message,
        created_at=order.created_at,
    )