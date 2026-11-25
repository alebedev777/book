from fastapi import APIRouter

from app.catalog import load_styles, load_themes
from app.schemas import StyleOut, ThemeOut

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/themes", response_model=list[ThemeOut])
async def list_themes() -> list[ThemeOut]:
    return load_themes()


@router.get("/styles", response_model=list[StyleOut])
async def list_styles() -> list[StyleOut]:
    return load_styles()