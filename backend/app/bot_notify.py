import io

import httpx

from app.config import get_settings


async def send_book_to_user(
    *,
    telegram_user_id: int,
    pdf_bytes: bytes,
    title: str,
    preview_images: list[bytes],
) -> None:
    settings = get_settings()
    token = settings.bot_token
    base = f"https://api.telegram.org/bot{token}"

    async with httpx.AsyncClient(timeout=120) as client:
        await client.post(
            f"{base}/sendMessage",
            json={
                "chat_id": telegram_user_id,
                "text": f"Книга «{title}» готова!",
            },
        )
        files = {"document": (f"{title}.pdf", pdf_bytes, "application/pdf")}
        await client.post(
            f"{base}/sendDocument",
            data={"chat_id": str(telegram_user_id)},
            files=files,
        )
        if preview_images:
            media = []
            buffers = []
            for i, img in enumerate(preview_images[:4]):
                field = f"photo{i}"
                buffers.append((field, (f"page_{i}.jpg", img, "image/jpeg")))
                media.append({"type": "photo", "media": f"attach://{field}"})
            multipart: list[tuple[str, tuple]] = [("chat_id", (None, str(telegram_user_id)))]
            multipart.append(("media", (None, __import__("json").dumps(media))))
            for b in buffers:
                multipart.append(b)
            await client.post(f"{base}/sendMediaGroup", files=multipart)


def send_book_to_user_sync(
    *,
    telegram_user_id: int,
    pdf_bytes: bytes,
    title: str,
    preview_images: list[bytes],
) -> None:
    settings = get_settings()
    token = settings.bot_token
    base = f"https://api.telegram.org/bot{token}"

    with httpx.Client(timeout=120) as client:
        client.post(
            f"{base}/sendMessage",
            json={"chat_id": telegram_user_id, "text": f"Книга «{title}» готова!"},
        )
        client.post(
            f"{base}/sendDocument",
            data={"chat_id": str(telegram_user_id)},
            files={"document": (f"{title}.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )