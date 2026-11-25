from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import engine
from app.models import Base
from app.routers import assets, catalog, orders, telegram
from app.observability import configure_langfuse
from app.storage import ensure_bucket


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_langfuse()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    ensure_bucket()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Book API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(catalog.router)
    app.include_router(assets.router)
    app.include_router(orders.router)
    app.include_router(telegram.router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "mini_app_url": settings.mini_app_url}

    return app


app = create_app()