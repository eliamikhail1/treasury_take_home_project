from pathlib import Path
import pandas as pd


REQUIRED_COLUMNS = [
    "labelName",
    "brandName",
    "class",
    "alcoholContent",
    "netContents",
    "address",
    "importOrigin",
    "healthWarning",
]


def parse_spreadsheet(file_path: str | Path) -> list[dict]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Spreadsheet not found: {path}")

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    else:
        raise ValueError("Spreadsheet must be a .csv, .xlsx, or .xls file.")

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Spreadsheet is missing required columns: {', '.join(missing_columns)}"
        )

    df = df[REQUIRED_COLUMNS]
    df = df.fillna("")

    rows = df.to_dict(orient="records")

    return rows