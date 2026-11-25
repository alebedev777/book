import mimetypes

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.storage import download_bytes

router = APIRouter(prefix="/api", tags=["assets"])


def _content_type(key: str) -> str:
    guessed, _ = mimetypes.guess_type(key)
    return guessed or "application/octet-stream"


@router.get("/assets/{key:path}")
async def get_asset(key: str) -> Response:
    if ".." in key or not key.startswith("orders/"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    try:
        data = download_bytes(key)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    return Response(content=data, media_type=_content_type(key))