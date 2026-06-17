# Treasury Take Home Project

A web application for checking alcohol label images against user-provided label information. The app supports both single-label validation and batch validation using a spreadsheet.

The application accepts uploaded alcohol label images, extracts visible text using OCR, compares the extracted text against expected label information, validates the required government warning header, and produces a validation report that can be exported as CSV, Excel, or PDF.

## Features

* Single image upload with manual form entry
* Batch image upload with spreadsheet input
* Spreadsheet parsing for CSV, XLSX, and XLS files
* Image filename matching against the `labelName` spreadsheet column
* Local OCR using Tesseract
* Field-level validation for:

  * Brand name
  * Class/type designation
  * Alcohol content
  * Net contents
  * Name and address
  * Import origin
  * Health warning statement
* Government warning validation:

  * Checks whether the warning begins with `GOVERNMENT WARNING`
  * Checks whether submitted warning text begins with `GOVERNMENT WARNING`
* Validation report page
* Export report as:

  * CSV
  * Excel
  * PDF
* Basic error handling for:

  * Missing spreadsheet columns
  * Unsupported file types
  * Missing image/spreadsheet filenames
  * Missing image-to-spreadsheet matches
  * OCR failures

## Project Structure

```text
alcohol-label-validator/
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── upload/
│   │   │   └── page.tsx
│   │   └── results/
│   │       └── page.tsx
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── single_label.py
│   │   │   └── batch_label.py
│   │   └── services/
│   │       ├── ocr.py
│   │       ├── spreadsheet.py
│   │       ├── validator.py
│   │       └── visual_checks.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── uploads/
│   ├── images/
│   └── spreadsheets/
│
└── README.md
```

## Tools Used

### Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* XLSX for Excel export
* jsPDF and jspdf-autotable for PDF export

### Backend

* FastAPI
* Uvicorn
* Pandas
* OpenPyXL
* Pillow
* pytesseract
* Tesseract OCR

### Deployment

* Frontend: Vercel
* Backend: Render using Docker

## Required Spreadsheet Format

Batch uploads require a spreadsheet with these exact columns:

```text
labelName
brandName
class
alcoholContent
netContents
address
importOrigin
healthWarning
```

The `labelName` value must match the image filename without the file extension.

Example:

```text
Image filename: test_vodka_pass.png
Spreadsheet labelName: test_vodka_pass
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/eliamikhail1/treasury_take_home_project.git
cd alcohol-label-validator
```

### 2. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Install Tesseract locally on macOS:

```bash
brew install tesseract
```

Run the backend:

```bash
uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

### 3. Frontend setup

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:3000
```

### 4. Frontend environment variable

Create:

```text
frontend/.env.local
```

Add:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Restart the frontend after editing `.env.local`.

## Running the App Locally

1. Start the backend:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

2. Start the frontend:

```bash
cd frontend
npm run dev
```

3. Open:

```text
http://localhost:3000/upload
```

4. Choose either:

   * Single Label
   * Batch Upload

5. Submit the form.

6. The app redirects to:

```text
http://localhost:3000/results
```

7. Export the report as CSV, Excel, or PDF.

## Deployment

### Backend on Render

The backend is designed to deploy with Docker because Tesseract requires a system-level package.

Render settings:

```text
Root Directory: backend
Environment: Docker
```

The backend `Dockerfile` installs:

```text
tesseract-ocr
```

and starts the server with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

No Gemini API key is required in the current local-OCR implementation.

### Frontend on Vercel

Vercel settings:

```text
Root Directory: frontend
Framework Preset: Next.js
```

Add this environment variable in Vercel:

```env
NEXT_PUBLIC_API_URL=https://treasurytakehomeproject.onrender.com
```

## Testing

### Generate a Test Dataset

Create a `test-data` folder and generate synthetic label images plus matching spreadsheets.

The test data should include:

* A passing label
* A label with lowercase or incorrectly formatted government warning
* A label with a mismatched brand name
* An extra image with no matching spreadsheet row
* A spreadsheet missing one required column
* An unsupported file type

### Example Spreadsheet

```csv
labelName,brandName,class,alcoholContent,netContents,address,importOrigin,healthWarning
test_vodka_pass,Example Vodka,Vodka,40% ABV,750 mL,"Example Bottling Co., Denver, CO",,"GOVERNMENT WARNING: According to the Surgeon General, women should not drink alcoholic beverages during pregnancy."
test_wine_bad_warning,Example Red Wine,Red Wine,13.5% ABV,750 mL,"Example Winery, Napa, CA",,"Government Warning: According to the Surgeon General, women should not drink alcoholic beverages during pregnancy."
test_beer_wrong_brand,Expected Beer Co.,Beer,5% ABV,12 FL OZ,"Expected Brewery, Austin, TX",,"GOVERNMENT WARNING: According to the Surgeon General, women should not drink alcoholic beverages during pregnancy."
```

### Expected Results

```text
test_vodka_pass
- Expected to mostly PASS

test_wine_bad_warning
- Expected to FAIL the government warning header check

test_beer_wrong_brand
- Expected to FAIL or WARNING on brand name depending on OCR output
```

## Application Approach

The app separates responsibilities into frontend, backend routes, and backend services.

### Frontend

The frontend handles:

* Upload UI
* Form input
* Batch file selection
* Calling the backend API
* Storing the latest validation report in `localStorage`
* Rendering validation results
* Exporting reports

### Backend

The backend handles:

* File receiving
* File type validation
* Temporary upload saving
* Spreadsheet parsing
* Image-to-row matching
* OCR
* Validation logic
* Returning structured report JSON

### Validation Strategy

Validation is currently text-based.

The OCR output is compared against the expected fields from either:

* the single-label form, or
* the batch spreadsheet row.

Exact matches produce `PASS`.

Close text matches can produce `WARNING`.

Missing or clearly different values produce `FAIL`.

## Assumptions

* Uploaded image filenames are meaningful and match spreadsheet `labelName` values.
* The spreadsheet uses the exact required column names.
* Images are JPG, JPEG, or PNG.
* The app is intended as a validation aid, not a final legal compliance determination.
* Local OCR quality depends heavily on image clarity, font size, contrast, and layout.
* The government warning header must begin with the exact text `GOVERNMENT WARNING`.

## Trade-offs and Limitations

### OCR Accuracy

The current implementation uses local Tesseract OCR. This avoids billing and API issues, but it is less accurate than cloud OCR or multimodal models on complex labels.

Tesseract may struggle with:

* curved bottle labels
* decorative fonts
* low-resolution images
* glare
* shadows
* rotated text
* small warning text
* busy label backgrounds

### Bold Detection

Bold detection is not fully implemented.

The app currently disables visual bold detection and returns a manual-review style result.

A better version would use image-region analysis or a multimodal model to determine whether `GOVERNMENT WARNING` is visually bold.

### Gemini Issue

Gemini was initially considered for OCR and bold detection. It would have allowed image-based text extraction and visual reasoning in one service.

However, Gemini API testing was blocked by Google project and billing issues, including:

* API enablement errors
* API key service restriction errors
* prepayment credit / billing configuration errors

Because deployment was time-sensitive, the app was switched to local Tesseract OCR. This removed the dependency on Gemini API keys, billing, quotas, and Google Cloud configuration.

### Storage

Uploaded files are currently saved to local backend folders:

```text
uploads/images
uploads/spreadsheets
```

This is acceptable for local development and MVP testing, but not ideal for production.

For production, use persistent cloud storage such as:

* AWS S3
* Google Cloud Storage
* Supabase Storage

### Deployment Storage Limitation

Render filesystem storage may be ephemeral depending on service type and configuration. Uploaded files should not be treated as permanent records unless persistent storage is configured.

### Compliance Limitation

This app can flag mismatches and likely problems. It does not replace legal review or official regulatory approval.

## Future Improvements

* Add real bold detection
* Add persistent database storage
* Add user accounts
* Add cloud file storage
* Add confidence scores from OCR
* Add manual review workflow
* Add downloadable audit package
* Add side-by-side image and validation view
* Add better fuzzy matching rules per field
* Add category-specific alcohol labeling rules
* Reintroduce Gemini or another multimodal model once billing/API setup is stable
