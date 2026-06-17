import re
from difflib import SequenceMatcher


REQUIRED_WARNING_HEADER = "GOVERNMENT WARNING"


FIELD_LABELS = {
    "brandName": "Brand Name",
    "class": "Class / Type",
    "className": "Class / Type",
    "alcoholContent": "Alcohol Content",
    "netContents": "Net Contents",
    "address": "Name and Address",
    "importOrigin": "Country of Origin",
    "healthWarning": "Health Warning Statement",
}


def normalize_text(value: str) -> str:
    value = value or ""
    value = value.upper()
    value = re.sub(r"\s+", " ", value)
    value = value.strip()
    return value


def find_best_ocr_line(expected: str, ocr_text: str) -> tuple[str, float]:
    expected_normalized = normalize_text(expected)

    if not expected_normalized:
        return "", 0.0

    lines = [
        line.strip()
        for line in ocr_text.splitlines()
        if line.strip()
    ]

    best_line = ""
    best_score = 0.0

    for line in lines:
        line_normalized = normalize_text(line)

        score = SequenceMatcher(
            None,
            expected_normalized,
            line_normalized,
        ).ratio()

        if score > best_score:
            best_score = score
            best_line = line

    return best_line, best_score


def validate_expected_field(
    field_key: str,
    expected_value: str,
    ocr_text: str,
) -> dict:
    expected_value = expected_value or ""

    if not expected_value.strip():
        return {
            "field": FIELD_LABELS.get(field_key, field_key),
            "expected": "",
            "found": "",
            "status": "SKIPPED",
            "reason": "No expected value was provided.",
        }

    expected_normalized = normalize_text(expected_value)
    ocr_normalized = normalize_text(ocr_text)

    if expected_normalized in ocr_normalized:
        return {
            "field": FIELD_LABELS.get(field_key, field_key),
            "expected": expected_value,
            "found": expected_value,
            "status": "PASS",
            "reason": "Expected value was found in OCR text.",
        }

    best_line, score = find_best_ocr_line(expected_value, ocr_text)

    if score >= 0.75:
        return {
            "field": FIELD_LABELS.get(field_key, field_key),
            "expected": expected_value,
            "found": best_line,
            "status": "WARNING",
            "reason": "Expected value was not found exactly, but a close OCR match was found.",
        }

    return {
        "field": FIELD_LABELS.get(field_key, field_key),
        "expected": expected_value,
        "found": best_line,
        "status": "FAIL",
        "reason": "Expected value was not found in OCR text.",
    }


def validate_government_warning_header(ocr_text: str) -> dict:
    lines = [
        line.strip()
        for line in ocr_text.splitlines()
        if line.strip()
    ]

    matching_line = ""

    for line in lines:
        if line.startswith(REQUIRED_WARNING_HEADER):
            matching_line = line
            break

    if matching_line:
        return {
            "field": "Government Warning Header",
            "expected": REQUIRED_WARNING_HEADER,
            "found": matching_line,
            "status": "PASS",
            "reason": "Health warning statement begins with GOVERNMENT WARNING.",
        }

    if REQUIRED_WARNING_HEADER in ocr_text:
        return {
            "field": "Government Warning Header",
            "expected": REQUIRED_WARNING_HEADER,
            "found": REQUIRED_WARNING_HEADER,
            "status": "FAIL",
            "reason": "GOVERNMENT WARNING appears in OCR text, but it does not begin a detected warning statement line.",
        }

    return {
        "field": "Government Warning Header",
        "expected": REQUIRED_WARNING_HEADER,
        "found": "",
        "status": "FAIL",
        "reason": "Health warning statement must begin with GOVERNMENT WARNING.",
    }


def validate_input_health_warning(expected_health_warning: str) -> dict:
    expected_health_warning = expected_health_warning or ""
    stripped = expected_health_warning.strip()

    if stripped.startswith(REQUIRED_WARNING_HEADER):
        return {
            "field": "Input Health Warning Format",
            "expected": f"{REQUIRED_WARNING_HEADER}...",
            "found": stripped,
            "status": "PASS",
            "reason": "Input health warning begins with GOVERNMENT WARNING.",
        }

    return {
        "field": "Input Health Warning Format",
        "expected": f"{REQUIRED_WARNING_HEADER}...",
        "found": stripped,
        "status": "FAIL",
        "reason": "The submitted health warning must begin exactly with GOVERNMENT WARNING.",
    }


def validate_government_warning_bold(
    bold_check: dict | None = None,
) -> dict:
    if not bold_check:
        return {
            "field": "Government Warning Bold",
            "expected": "GOVERNMENT WARNING must be bold",
            "found": "Not checked",
            "status": "WARNING",
            "reason": "Bold detection was not run.",
        }

    if bold_check.get("boldDetected"):
        return {
            "field": "Government Warning Bold",
            "expected": "GOVERNMENT WARNING must be bold",
            "found": "Bold detected",
            "status": "PASS",
            "reason": bold_check.get("reason", "Bold text was detected."),
        }

    return {
        "field": "Government Warning Bold",
        "expected": "GOVERNMENT WARNING must be bold",
        "found": "Bold not detected",
        "status": "FAIL",
        "reason": bold_check.get(
            "reason",
            "GOVERNMENT WARNING was not detected as bold.",
        ),
    }


def validate_label_text(
    ocr_text: str,
    expected_fields: dict | None = None,
    bold_check: dict | None = None,
) -> list[dict]:
    expected_fields = expected_fields or {}

    validations = [
        validate_government_warning_header(ocr_text),
        validate_input_health_warning(expected_fields.get("healthWarning", "")),
        validate_government_warning_bold(bold_check),
    ]

    fields_to_validate = [
        "brandName",
        "class",
        "className",
        "alcoholContent",
        "netContents",
        "address",
        "importOrigin",
        "healthWarning",
    ]

    for field_key in fields_to_validate:
        if field_key in expected_fields:
            validations.append(
                validate_expected_field(
                    field_key=field_key,
                    expected_value=expected_fields.get(field_key, ""),
                    ocr_text=ocr_text,
                )
            )

    return validations