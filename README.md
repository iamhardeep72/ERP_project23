# 🩺 MediScan — AI Medical Report Analyzer

Upload any blood test or lab report (PDF or image) and get instant AI-powered insights showing which values are **High**, **Low**, or **Normal**.

---

## 📁 Project Structure

```
medical-report-analyzer/
├── frontend/
│   └── index.html          ← Beautiful animated single-page UI
│
├── backend/
│   ├── main.py             ← FastAPI app with /analyze endpoint
│   ├── extractor.py        ← PDF & image text extraction (OCR)
│   ├── analyzer.py         ← Claude AI analysis
│   ├── requirements.txt    ← Python dependencies
│   └── .env.example        ← Environment variable template
│
└── README.md               ← You are here
```

---

## ⚙️ Prerequisites

Before you start, make sure you have:

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.9+ | https://python.org |
| Tesseract OCR | Any | See below |
| Anthropic API key | — | https://console.anthropic.com |

---

## 🚀 Step-by-Step Setup

### Step 1 — Install Tesseract OCR (system binary)

Tesseract is required to read text from image files and scanned PDFs.

**macOS (Homebrew):**
```bash
brew install tesseract
```

**Ubuntu / Debian:**
```bash
sudo apt update && sudo apt install -y tesseract-ocr
```

**Windows:**
Download and run the installer from:
https://github.com/UB-Mannheim/tesseract/wiki

> **Windows users:** After installing, add Tesseract to your PATH, or set it explicitly in `extractor.py`:
> ```python
> pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
> ```

Verify installation:
```bash
tesseract --version
```

---

### Step 2 — Set up the Python environment

```bash
# Navigate to the backend directory
cd medical-report-analyzer/backend

# Create a virtual environment (strongly recommended)
python -m venv venv

# Activate it
# macOS / Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 3 — Configure your API key

```bash
# Copy the example env file
cp .env.example .env

# Open .env in any text editor and add your key:
# ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

Get your API key at: https://console.anthropic.com

---

### Step 4 — Start the backend server

```bash
# Make sure you're in the backend/ directory with venv active
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO │ Started server process
INFO │ Uvicorn running on http://127.0.0.1:8000
```

Test it works:
```bash
curl http://localhost:8000
# → {"status":"ok","service":"MediScan API"}
```

You can also explore the auto-generated API docs at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:**      http://localhost:8000/redoc

---

### Step 5 — Open the frontend

Simply open the HTML file in your browser:

```bash
# macOS
open ../frontend/index.html

# Linux
xdg-open ../frontend/index.html

# Windows — double-click the file, or:
start ../frontend/index.html
```

> **Note:** The frontend expects the backend at `http://localhost:8000`.
> If you change the port, update the `API_BASE` constant at the top of `index.html`.

---

## 🧪 Testing the API Directly

You can test the `/analyze` endpoint with `curl`:

```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@/path/to/your/report.pdf" \
  -H "Accept: application/json"
```

**Example response:**
```json
{
  "high_values": [
    {
      "name": "Glucose",
      "value": "130",
      "unit": "mg/dL",
      "normal_range": "70–99 mg/dL"
    }
  ],
  "low_values": [
    {
      "name": "Hemoglobin",
      "value": "10.2",
      "unit": "g/dL",
      "normal_range": "13.5–17.5 g/dL"
    }
  ],
  "normal_values": [
    {
      "name": "Platelet Count",
      "value": "250000",
      "unit": "/μL",
      "normal_range": "150,000–400,000 /μL"
    }
  ]
}
```

---

## 🔍 How It Works

```
User uploads PDF/Image
        ↓
FastAPI receives file (/analyze endpoint)
        ↓
extractor.py reads the file:
  • PDF  → PyMuPDF extracts text layer (fast)
           If scanned → Tesseract OCR
  • Image → Tesseract OCR with pre-processing
        ↓
analyzer.py sends text to Claude AI
  (with a medical analysis system prompt)
        ↓
Claude returns structured JSON
        ↓
Frontend renders:
  🔴 High values  (red)
  🟡 Low values   (yellow)
  🟢 Normal values (green)
```

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| `TesseractNotFoundError` | Install Tesseract binary (Step 1) |
| `AuthenticationError` | Check your `ANTHROPIC_API_KEY` in `.env` |
| CORS error in browser | Make sure the backend is running on port 8000 |
| Empty results | The file may have no readable text; try a clearer scan |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` with venv active |

---

## ⚠️ Medical Disclaimer

This tool is for **informational and educational purposes only**. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider with any questions about your test results.

---

## 📜 License

MIT — free to use and modify for personal and commercial projects.
