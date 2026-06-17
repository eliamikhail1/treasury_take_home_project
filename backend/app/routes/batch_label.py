from pathlib import Path
from fastapi import APIRouter, UploadFile, File

from app.services.spreadsheet import parse_spreadsheet
from app.services.ocr import extract_text_from_image
from app.services.validator import validate_label_text
from app.services.visual_checks import check_government_warning_bold

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]

IMAGE_UPLOAD_DIR = BASE_DIR / "uploads" / "images"
SPREADSHEET_UPLOAD_DIR = BASE_DIR / "uploads" / "spreadsheets"

IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SPREADSHEET_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_SPREADSHEET_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def is_allowed_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_IMAGE_EXTENSIONS


def is_allowed_spreadsheet(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_SPREADSHEET_EXTENSIONS


@router.post("/batch-label-check")
async def batch_label_check(
    images: list[UploadFile] = File(...),
    spreadsheet: UploadFile = File(...),
):
    if not images:
        return {
            "status": "ERROR",
            "mode": "batch",
            "errorType": "NO_IMAGES_UPLOADED",
            "error": "No label images were uploaded.",
            "report": [],
        }

    if not spreadsheet.filename:
        return {
            "status": "ERROR",
            "mode": "batch",
            "errorType": "MISSING_SPREADSHEET_FILENAME",
            "error": "Uploaded spreadsheet has no filename.",
            "report": [],
        }

    if not is_allowed_spreadsheet(spreadsheet.filename):
        return {
            "status": "ERROR",
            "mode": "batch",
            "spreadsheetFilename": spreadsheet.filename,
            "errorType": "UNSUPPORTED_SPREADSHEET_TYPE",
            "error": "Unsupported spreadsheet type. Use .csv, .xlsx, or .xls.",
            "report": [],
        }

    saved_images = []

    for image in images:
        if not image.filename:
            saved_images.append(
                {
                    "filename": "",
                    "labelName": "",
                    "path": None,
                    "error": "Uploaded image has no filename.",
                    "errorType": "MISSING_IMAGE_FILENAME",
                }
            )
            continue

        if not is_allowed_image(image.filename):
            saved_images.append(
                {
                    "filename": image.filename,
                    "labelName": Path(image.filename).stem,
                    "path": None,
                    "error": "Unsupported image type. Use .jpg, .jpeg, or .png.",
                    "errorType": "UNSUPPORTED_IMAGE_TYPE",
                }
            )
            continue

        image_path = IMAGE_UPLOAD_DIR / image.filename

        try:
            contents = await image.read()

            with open(image_path, "wb") as file:
                file.write(contents)

            saved_images.append(
                {
                    "filename": image.filename,
                    "labelName": Path(image.filename).stem,
                    "path": image_path,
                    "error": None,
                    "errorType": None,
                }
            )

        except Exception as error:
            saved_images.append(
                {
                    "filename": image.filename,
                    "labelName": Path(image.filename).stem,
                    "path": None,
                    "error": str(error),
                    "errorType": "FILE_SAVE_FAILED",
                }
            )

    spreadsheet_path = SPREADSHEET_UPLOAD_DIR / spreadsheet.filename

    try:
        spreadsheet_contents = await spreadsheet.read()

        with open(spreadsheet_path, "wb") as file:
            file.write(spreadsheet_contents)

    except Exception as error:
        return {
            "status": "ERROR",
            "mode": "batch",
            "spreadsheetFilename": spreadsheet.filename,
            "errorType": "SPREADSHEET_SAVE_FAILED",
            "error": str(error),
            "report": [],
        }

    try:
        spreadsheet_rows = parse_spreadsheet(spreadsheet_path)

    except Exception as error:
        return {
            "status": "ERROR",
            "mode": "batch",
            "spreadsheetFilename": spreadsheet.filename,
            "savedSpreadsheetPath": str(spreadsheet_path),
            "errorType": "SPREADSHEET_PARSE_FAILED",
            "error": str(error),
            "report": [],
        }

    spreadsheet_lookup = {
        row["labelName"]: row
        for row in spreadsheet_rows
    }

    report = []

    for image_data in saved_images:
        image_filename = image_data["filename"]
        label_name = image_data["labelName"]
        image_path = image_data["path"]

        if image_data["error"]:
            report.append(
                {
                    "imageFilename": image_filename,
                    "labelName": label_name,
                    "matched": False,
                    "status": "ERROR",
                    "errorType": image_data["errorType"],
                    "error": image_data["error"],
                    "ocrText": "",
                    "boldCheck": None,
                    "validations": [],
                }
            )
            continue

        spreadsheet_row = spreadsheet_lookup.get(label_name)

        if spreadsheet_row is None:
            report.append(
                {
                    "imageFilename": image_filename,
                    "labelName": label_name,
                    "matched": False,
                    "status": "FAIL",
                    "errorType": "NO_MATCHING_SPREADSHEET_ROW",
                    "error": "No matching spreadsheet row found.",
                    "ocrText": "",
                    "boldCheck": None,
                    "validations": [],
                }
            )
            continue

        try:
            ocr_text = extract_text_from_image(image_path)

        except Exception as error:
            report.append(
                {
                    "imageFilename": image_filename,
                    "labelName": label_name,
                    "matched": True,
                    "status": "ERROR",
                    "spreadsheetRow": spreadsheet_row,
                    "errorType": "OCR_FAILED_OR_GEMINI_LIMIT",
                    "error": str(error),
                    "ocrText": "",
                    "boldCheck": None,
                    "validations": [],
                }
            )
            continue

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
            spreadsheet_row,
            bold_check,
        )

        has_failures = any(
            validation["status"] == "FAIL"
            for validation in validations
        )

        report.append(
            {
                "imageFilename": image_filename,
                "labelName": label_name,
                "matched": True,
                "status": "FAIL" if has_failures else "PASS",
                "spreadsheetRow": spreadsheet_row,
                "ocrText": ocr_text,
                "boldCheck": bold_check,
                "validations": validations,
            }
        )

    has_errors = any(item["status"] == "ERROR" for item in report)
    has_failures = any(item["status"] == "FAIL" for item in report)

    overall_status = "ERROR" if has_errors else "FAIL" if has_failures else "PASS"

    return {
        "status": overall_status,
        "mode": "batch",
        "imageCount": len(images),
        "spreadsheetFilename": spreadsheet.filename,
        "spreadsheetRowCount": len(spreadsheet_rows),
        "report": report,
    }