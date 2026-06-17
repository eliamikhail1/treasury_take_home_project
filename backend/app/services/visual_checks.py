from pathlib import Path


def check_government_warning_bold(image_path: str | Path) -> dict:
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    return {
        "boldDetected": False,
        "confidence": "low",
        "reason": "Bold detection is disabled in local OCR mode. Manual review required.",
    }