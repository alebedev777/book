import io
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.orders_service import create_order, get_order_for_user, order_to_out
from app.schemas import OrderCreateResponse, OrderOut
from app.storage import new_order_prefix, upload_bytes
from app.telegram_auth import validate_init_data
from app.worker.tasks import generate_book_task

router = APIRouter(prefix="/api", tags=["orders"])

ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD = 10 * 1024 * 1024


@router.post("/orders", response_model=OrderCreateResponse)
async def post_order(
    init_data: str = Form(...),
    style_id: str = Form(...),
    child_name: str = Form(...),
    child_age: int | None = Form(None),
    theme_id: str | None = Form(None),
    custom_theme: str | None = Form(None),
    consent: str = Form(...),
    photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> OrderCreateResponse:
    if consent.lower() not in ("true", "1", "yes", "on"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="consent_required")

    settings = get_settings()
    auth = validate_init_data(init_data, settings.bot_token)
    telegram_user_id = auth["telegram_user_id"]

    if photo.content_type not in ALLOWED_IMAGE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_image_type")

    contents = await photo.read()
    if len(contents) > MAX_UPLOAD:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file_too_large")

    order_id = uuid.uuid4()
    photo_key = f"{new_order_prefix(order_id)}/photo.jpg"
    upload_bytes(contents, photo_key, photo.content_type or "image/jpeg")

    try:
        order = await create_order(
            db,
            order_id=order_id,
            telegram_user_id=telegram_user_id,
            theme_id=theme_id,
            custom_theme=custom_theme,
            style_id=style_id,
            child_name=child_name,
            child_age=child_age,
            photo_key=photo_key,
        )
    except ValueError as e:
        code = str(e)
        detail_map = {
            "rate_limit": "У вас уже есть книга в процессе создания.",
            "invalid_style": "Неизвестный стиль.",
            "invalid_theme": "Неизвестная тема.",
            "theme_conflict": "Укажите либо тему из списка, либо свою.",
            "theme_required": "Выберите или введите тему.",
            "theme_rejected": "Тема не прошла проверку безопасности.",
        }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_map.get(code, code),
        ) from e

    generate_book_task.delay(str(order.id))
    return OrderCreateResponse(id=order.id, status=order.status)


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: uuid.UUID,
    init_data: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> OrderOut:
    settings = get_settings()
    auth = validate_init_data(init_data, settings.bot_token)
    order = await get_order_for_user(db, order_id, auth["telegram_user_id"])
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return order_to_out(order)