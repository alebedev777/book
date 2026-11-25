"""Локальный прогон заказа без Telegram.

Usage:
  uv run python scripts/run_sample_order.py /path/to/photo.jpg [имя]
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Order
from app.orders_service import create_order
from app.storage import new_order_prefix, public_url, upload_bytes
from app.worker.tasks import SyncSession, generate_book_task


async def create(photo_path: Path, child_name: str, theme_id: str, style_id: str) -> uuid.UUID:
    order_id = uuid.uuid4()
    upload_bytes(
        photo_path.read_bytes(),
        f"{new_order_prefix(order_id)}/photo.jpg",
        "image/jpeg",
    )
    async with SessionLocal() as db:
        await create_order(
            db,
            order_id=order_id,
            telegram_user_id=900006,
            theme_id=theme_id,
            custom_theme=None,
            style_id=style_id,
            child_name=child_name,
            child_age=None,
            photo_key=f"{new_order_prefix(order_id)}/photo.jpg",
        )
    return order_id


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: uv run python scripts/run_sample_order.py <photo.jpg> [имя]")
    photo = Path(sys.argv[1])
    if not photo.is_file():
        sys.exit(f"File not found: {photo}")
    child_name = sys.argv[2] if len(sys.argv) > 2 else "Артем"
    theme_id = sys.argv[3] if len(sys.argv) > 3 else "friendship"
    style_id = sys.argv[4] if len(sys.argv) > 4 else "flat_graphic"

    order_id = asyncio.run(create(photo, child_name, theme_id, style_id))
    print(f"order_id={order_id} theme={theme_id} style={style_id} child={child_name}")

    generate_book_task.run(str(order_id))

    with SyncSession() as session:
        order = session.get(Order, order_id)
        if not order:
            sys.exit("order missing after task")
        print(f"status={order.status} progress={order.progress_percent}")
        if order.error_message:
            print(f"error={order.error_message}")
        if order.pdf_key:
            print(f"pdf_url={public_url(order.pdf_key)}")
        for key in order.preview_keys or []:
            print(f"preview={public_url(key)}")


if __name__ == "__main__":
    main()