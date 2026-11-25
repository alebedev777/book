import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def webapp_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Создать книгу", web_app=WebAppInfo(url=url))],
        ]
    )


async def on_start(message: Message) -> None:
    settings = get_settings()
    await message.answer(
        "Привет! Я помогу создать персональную детскую книгу с важным жизненным уроком.\n\n"
        "Откройте мини-приложение, выберите тему, стиль, имя ребёнка и фото — книга придёт сюда в PDF.",
        reply_markup=webapp_keyboard(settings.mini_app_url),
    )


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required")

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.message.register(on_start, CommandStart())

    @dp.message(F.web_app_data)
    async def on_web_app_data(message: Message) -> None:
        await message.answer("Спасибо! Когда книга будет готова, я пришлю PDF в этот чат.")

    logger.info("Bot polling started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())