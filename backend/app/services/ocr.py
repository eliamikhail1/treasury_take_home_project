from pathlib import Path

import pytesseract
from PIL import Image


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def extract_text_from_image(image_path: str | Path) -> str:
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    if path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Only .jpg, .jpeg, and .png images are supported.")

    try:
        image = Image.open(path)
        text = pytesseract.image_to_string(image)
        return text or ""

    except Exception as error:
        raise RuntimeError(f"Local OCR failed: {str(error)}")