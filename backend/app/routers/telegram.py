"""Telegram bot webhook (optional; bot/main.py uses long polling by default)."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(request: Request):
    payload = await request.json()
    return {"ok": True, "received": bool(payload)}