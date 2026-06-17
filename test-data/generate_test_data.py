from pathlib import Path
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

rows = [
    {
        "labelName": "test_vodka_pass",
        "brandName": "Example Vodka",
        "class": "Vodka",
        "alcoholContent": "40% ABV",
        "netContents": "750 mL",
        "address": "Example Bottling Co., Denver, CO",
        "importOrigin": "",
        "healthWarning": "GOVERNMENT WARNING: According to the Surgeon General, women should not drink alcoholic beverages during pregnancy.",
    },
    {
        "labelName": "test_wine_bad_warning",
        "brandName": "Example Red Wine",
        "class": "Red Wine",
        "alcoholContent": "13.5% ABV",
        "netContents": "750 mL",
        "address": "Example Winery, Napa, CA",
        "importOrigin": "",
        "healthWarning": "Government Warning: According to the Surgeon General, women should not drink alcoholic beverages during pregnancy.",
    },
    {
        "labelName": "test_beer_wrong_brand",
        "brandName": "Expected Beer Co.",
        "class": "Beer",
        "alcoholContent": "5% ABV",
        "netContents": "12 FL OZ",
        "address": "Expected Brewery, Austin, TX",
        "importOrigin": "",
        "healthWarning": "GOVERNMENT WARNING: According to the Surgeon General, women should not drink alcoholic beverages during pregnancy.",
    },
]

def make_label(row, filename, override_brand=None, lowercase_warning=False):
    img = Image.new("RGB", (900, 650), "white")
    draw = ImageDraw.Draw(img)

    try:
        font_big = ImageFont.truetype("Arial.ttf", 42)
        font_regular = ImageFont.truetype("Arial.ttf", 26)
        font_bold = ImageFont.truetype("Arial Bold.ttf", 28)
    except:
        font_big = ImageFont.load_default()
        font_regular = ImageFont.load_default()
        font_bold = ImageFont.load_default()

    brand = override_brand or row["brandName"]
    warning = row["healthWarning"]

    if lowercase_warning:
        warning = warning.replace("GOVERNMENT WARNING", "Government Warning")

    lines = [
        brand,
        row["class"],
        row["alcoholContent"],
        row["netContents"],
        row["address"],
        row["importOrigin"],
        warning,
    ]

    y = 60
    draw.text((60, y), lines[0], fill="black", font=font_big)
    y += 90

    for line in lines[1:6]:
        if line:
            draw.text((60, y), line, fill="black", font=font_regular)
            y += 45

    y += 20
    warning_header = warning.split(":")[0] + ":"
    warning_rest = warning[len(warning_header):].strip()

    draw.text((60, y), warning_header, fill="black", font=font_bold)
    y += 40
    draw.text((60, y), warning_rest[:80], fill="black", font=font_regular)

    img.save(IMAGE_DIR / filename)

make_label(rows[0], "test_vodka_pass.png")
make_label(rows[1], "test_wine_bad_warning.png", lowercase_warning=True)
make_label(rows[2], "test_beer_wrong_brand.png", override_brand="Different Beer Co.")

df = pd.DataFrame(rows)
df.to_csv(BASE_DIR / "test_labels.csv", index=False)
df.to_excel(BASE_DIR / "test_labels.xlsx", index=False)

print("Generated:")
print(BASE_DIR / "test_labels.csv")
print(BASE_DIR / "test_labels.xlsx")
print(IMAGE_DIR)