import json
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


def check_government_warning_bold(image_path: str | Path) -> dict:
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
            Analyze this alcohol label image.

            Determine whether the exact phrase "GOVERNMENT WARNING" appears in bold text.

            Return ONLY valid JSON in this exact format:
            {
              "boldDetected": true,
              "confidence": "high",
              "reason": "The phrase GOVERNMENT WARNING appears visually bold compared with the surrounding warning text."
            }

            Rules:
            - boldDetected must be true only if "GOVERNMENT WARNING" is visibly bold.
            - If the phrase is not visible, return boldDetected false.
            - If the phrase is visible but not clearly bold, return boldDetected false.
            - confidence must be one of: "high", "medium", "low".
            """,
        ],
    )

    raw_text = response.text or ""

    try:
        parsed = json.loads(_extract_json(raw_text))
    except json.JSONDecodeError:
        return {
            "boldDetected": False,
            "confidence": "low",
            "reason": "Gemini did not return valid JSON for bold detection.",
        }

    return {
        "boldDetected": bool(parsed.get("boldDetected", False)),
        "confidence": parsed.get("confidence", "low"),
        "reason": parsed.get("reason", ""),
    }


def _get_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in [".jpg", ".jpeg"]:
        return "image/jpeg"

    if suffix == ".png":
        return "image/png"

    raise ValueError("Only .jpg, .jpeg, and .png images are supported.")


def _extract_json(text: str) -> str:
    text = text.strip()

    if text.startswith("```json"):
        text = text.removeprefix("```json").removesuffix("```").strip()

    if text.startswith("```"):
        text = text.removeprefix("```").removesuffix("```").strip()

    return text