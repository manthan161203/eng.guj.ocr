# OCR Translation API (English/Gujarati)

FastAPI application for:
- Text translation
- Image OCR + translation
- Audio transcription (Speech-to-Text)
- Text-to-Speech audio generation
- Exporting translation results as PDF/TXT

The web UI is served from `static/index.html` by the same API service.

## Project Structure

```text
.
├── advanced_ocr_api.py             # FastAPI app + OCR/STT/TTS logic
├── static/index.html               # Frontend UI
├── requirements_advanced_ocr.txt   # Python dependencies
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Features

- OCR engines: `easyocr`, `paddleocr`, `tesseract`, and `auto` selection
- Translation via `googletrans`
- Speech-to-Text via `faster-whisper`
- Text-to-Speech via `gTTS`
- Export as `pdf` or `txt`
- CORS enabled (`*`) for development/integration

## Requirements

### System packages (for local non-Docker run)

Install at least:
- `ffmpeg`
- `tesseract-ocr`
- language packs used by Tesseract (`eng`, `hin`, `guj`)
- OpenCV runtime libs (`libgl1`, `libglib2.0-0` on Debian/Ubuntu)

Docker image already installs required OS packages.

### Python

- Python `3.10`
- Install dependencies:

```bash
pip install -r requirements_advanced_ocr.txt
```

## Run

### Option 1: Docker Compose (recommended)

```bash
docker compose up --build
```

Service will be available at:
- UI: `http://localhost:8001/`
- Swagger docs: `http://localhost:8001/docs`
- API info: `http://localhost:8001/api-info`

### Option 2: Local Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_advanced_ocr.txt
python advanced_ocr_api.py
```

Service will be available at:
- UI: `http://localhost:8000/`
- Swagger docs: `http://localhost:8000/docs`

## API Endpoints

### Health / metadata

- `GET /` - Serves UI (`static/index.html`)
- `GET /api-info` - API metadata and endpoint list
- `GET /available-engines` - Installed OCR engines and recommendations

### Translation

- `POST /translate-text?target_lang=gu`
  - JSON body: `{ "text": "..." }`
- `POST /translate-image?ocr_engine=auto&target_lang=gu`
  - multipart form-data: `file=<image>`
- `POST /translate`
  - Unified endpoint accepting either:
    - form `text=...`
    - or form `file=<image>`

### Audio

- `POST /transcribe-audio`
  - multipart form-data:
    - `file=<audio>`
    - optional `language=<lang_code>`
- `GET /audio/{audio_id}?text=...&lang=gu`
  - Generates/serves MP3 for given text

### Export

- `POST /export`
  - multipart form-data fields:
    - `original_text`
    - `translated_text`
    - `src_lang`
    - `dest_lang`
    - `format` = `pdf` or `txt`

## cURL Examples

### Translate text

```bash
curl -X POST "http://localhost:8000/translate-text?target_lang=gu" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world"}'
```

### OCR + translate image

```bash
curl -X POST "http://localhost:8000/translate-image?ocr_engine=easyocr&target_lang=gu" \
  -F "file=@sample.jpg"
```

### Transcribe audio

```bash
curl -X POST "http://localhost:8000/transcribe-audio" \
  -F "file=@sample.wav" \
  -F "language=en"
```

### Export PDF

```bash
curl -X POST "http://localhost:8000/export" \
  -F "original_text=hello" \
  -F "translated_text=હેલો" \
  -F "src_lang=en" \
  -F "dest_lang=gu" \
  -F "format=pdf" \
  --output translation.pdf
```

## Environment Variables

Common variables used by this app:
- `PORT` (default: `8000`)
- `EASYOCR_MODULE_PATH` (default in Docker: `/root/.EasyOCR`)
- `WHISPER_MODEL` (default: `base`)
- `WHISPER_DEVICE` (default: `cpu`)
- `WHISPER_COMPUTE_TYPE` (default: `int8`)

## Notes / Limitations

- First run can be slower due to model downloads (EasyOCR / Whisper).
- `googletrans` depends on Google Translate web behavior and may fail intermittently.
- PDF export uses ReportLab default fonts; Gujarati/Hindi rendering in PDFs can be limited without custom Unicode font registration.
- Generated audio/transient files are stored under `temp/`.
