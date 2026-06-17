import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in backend/.env")

client = genai.Client(api_key=GEMINI_API_KEY)


def extract_text_from_image(image_path: str | Path) -> str:
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    image_bytes = path.read_bytes()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=_get_mime_type(path),
            ),
            """
            Extract all visible text from this alcohol label image.

            Return only the raw text found on the label.
            Do not summarize.
            Do not explain.
            Preserve line breaks as much as possible.
            """,
        ],
    )

    return response.text or ""


def _get_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in [".jpg", ".jpeg"]:
        return "image/jpeg"

    if suffix == ".png":
        return "image/png"

    raise ValueError("Only .jpg, .jpeg, and .png images are supported.")