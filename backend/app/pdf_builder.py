import io

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from app.schemas import StoryBook


def build_pdf(
    *,
    book: StoryBook,
    page_images: list[bytes],
    cover_image: bytes | None = None,
) -> bytes:
    if len(page_images) != len(book.pages):
        raise ValueError("page_image_mismatch")

    buf = io.BytesIO()
    w, h = A4
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(book.title)

    margin = 0.6 * cm

    if cover_image:
        _draw_image_fullwidth(c, cover_image, margin, margin, w - 2 * margin, h - 2 * margin)
        c.showPage()

    for img_bytes in page_images:
        _draw_image_fullwidth(c, img_bytes, margin, margin, w - 2 * margin, h - 2 * margin)
        c.showPage()

    c.save()
    return buf.getvalue()


def _draw_image_fullwidth(c: canvas.Canvas, data: bytes, x: float, y: float, width: float, height: float):
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img_buf = io.BytesIO()
    img.save(img_buf, format="JPEG", quality=88)
    img_buf.seek(0)
    from reportlab.lib.utils import ImageReader

    c.drawImage(ImageReader(img_buf), x, y, width=width, height=height, preserveAspectRatio=True, anchor="sw")