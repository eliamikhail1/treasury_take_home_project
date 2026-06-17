from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form

from app.services.ocr import extract_text_from_image
from app.services.validator import validate_label_text
from app.services.visual_checks import check_government_warning_bold

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
IMAGE_UPLOAD_DIR = BASE_DIR / "uploads" / "images"
IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def is_allowed_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_IMAGE_EXTENSIONS


@router.post("/single-label-check")
async def single_label_check(
    image: UploadFile = File(...),
    brandName: str = Form(...),
    className: str = Form(...),
    alcoholContent: str = Form(...),
    netContents: str = Form(...),
    address: str = Form(...),
    importOrigin: str = Form(""),
    healthWarning: str = Form(...),
):
    input_fields = {
        "brandName": brandName,
        "className": className,
        "alcoholContent": alcoholContent,
        "netContents": netContents,
        "address": address,
        "importOrigin": importOrigin,
        "healthWarning": healthWarning,
    }

    if not image.filename:
        return {
            "status": "ERROR",
            "mode": "single",
            "errorType": "MISSING_IMAGE_FILENAME",
            "error": "Uploaded image has no filename.",
            "fields": input_fields,
            "ocrText": "",
            "boldCheck": None,
            "validations": [],
        }

    if not is_allowed_image(image.filename):
        return {
            "status": "ERROR",
            "mode": "single",
            "imageFilename": image.filename,
            "errorType": "UNSUPPORTED_IMAGE_TYPE",
            "error": "Unsupported image type. Use .jpg, .jpeg, or .png.",
            "fields": input_fields,
            "ocrText": "",
            "boldCheck": None,
            "validations": [],
        }

    image_path = IMAGE_UPLOAD_DIR / image.filename

    try:
        contents = await image.read()

        with open(image_path, "wb") as file:
            file.write(contents)

    except Exception as error:
        return {
            "status": "ERROR",
            "mode": "single",
            "imageFilename": image.filename,
            "savedImagePath": str(image_path),
            "errorType": "FILE_SAVE_FAILED",
            "error": str(error),
            "fields": input_fields,
            "ocrText": "",
            "boldCheck": None,
            "validations": [],
        }

    try:
        ocr_text = extract_text_from_image(image_path)
    except Exception as error:
        return {
            "status": "ERROR",
            "mode": "single",
            "imageFilename": image.filename,
            "savedImagePath": str(image_path),
            "errorType": "OCR_FAILED_OR_GEMINI_LIMIT",
            "error": str(error),
            "fields": input_fields,
            "ocrText": "",
            "boldCheck": None,
            "validations": [],
        }

    try:
        bold_check = check_government_warning_bold(image_path)
    except Exception as error:
        bold_check = {
            "boldDetected": False,
            "confidence": "low",
            "reason": f"Bold detection failed: {str(error)}",
        }

    validations = validate_label_text(
        ocr_text,
        input_fields,
        bold_check,
    )

    has_failures = any(
        validation["status"] == "FAIL"
        for validation in validations
    )

    return {
        "status": "FAIL" if has_failures else "PASS",
        "mode": "single",
        "imageFilename": image.filename,
        "savedImagePath": str(image_path),
        "fields": input_fields,
        "ocrText": ocr_text,
        "boldCheck": bold_check,
        "validations": validations,
    }