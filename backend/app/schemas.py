import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models import OrderStatus


class ThemeOut(BaseModel):
    id: str
    title_ru: str
    learning_goal: str
    age_range: str
    archetype: str = ""
    jungian_mechanism: str = ""
    story_beats: list[str] = Field(default_factory=list)


class StyleOut(BaseModel):
    id: str
    title_ru: str


class OrderCreateResponse(BaseModel):
    id: uuid.UUID
    status: OrderStatus


class OrderOut(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    progress_percent: int
    page_count: int | None = None
    preview_urls: list[str] | None = None
    pdf_url: str | None = None
    error_message: str | None = None
    created_at: datetime


class StoryPage(BaseModel):
    page: int
    text: str
    illustration_scene: str


class StoryBook(BaseModel):
    title: str
    hero_name: str
    pages: list[StoryPage]


class GenerationProgress(BaseModel):
    status: Literal[
        "generating_text",
        "generating_images",
        "building_pdf",
        "done",
        "failed",
    ]
    progress_percent: int = Field(ge=0, le=100)