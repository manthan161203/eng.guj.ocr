# OCR + Translation Web App

A powerful, full-featured web application for optical character recognition (OCR), multi-language translation, audio transcription, and text-to-speech conversion. Built with FastAPI and featuring a modern, responsive web interface.

**Key Features:**
- 🔍 **Multi-Engine OCR**: EasyOCR, PaddleOCR, and Tesseract support
- 🌍 **Multi-Language**: English, Hindi, and Gujarati (easily extensible)
- 📝 **Text Translation**: Real-time translation between supported languages
- 🖼️ **Image OCR**: Extract and translate text from images
- 🎤 **Speech-to-Text**: Audio transcription using Faster Whisper
- 🔊 **Text-to-Speech**: Generate audio from translated text
- 📥 **Export**: Save results as PDF or TXT files
- 🎨 **Modern UI**: Responsive web interface with dark mode

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
docker compose up --build
```

Then open:
- **UI**: `http://localhost:8001`
- **API Docs**: `http://localhost:8001/docs`
- **API Info**: `http://localhost:8001/api-info`

### Option 2: Local Python Installation

```bash
# Clone/navigate to project directory
cd /path/to/project

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements_advanced_ocr.txt

# Run the server
python advanced_ocr_api.py
```

Then open `http://localhost:8000`

---

## Architecture

### Backend
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn
- **OCR Engines**: EasyOCR, PaddleOCR, Tesseract
- **Translation**: GoogleTrans
- **Speech Processing**: Faster Whisper, gTTS
- **PDF Generation**: ReportLab
- **Image Processing**: Pillow, OpenCV

### Frontend
- **Architecture**: Single-Page Application (SPA)
- **HTML/CSS/JS**: Vanilla JavaScript with Tailwind CSS
- **Features**: Multi-tab interface, real-time preview, progress tracking

---

## API Documentation

### Core Endpoints

#### Health & Info
- `GET /` - Serve frontend UI
- `GET /api-info` - Get API capabilities and version
- `GET /available-engines` - List available OCR engines and languages

#### Text Operations
- `POST /translate-text` - Translate plain text
- `POST /translate` - Alternative translate endpoint

#### Image Operations
- `POST /translate-image` - OCR + translate image
  - Supports: PNG, JPEG, GIF, BMP, WebP
  - Returns: Extracted text, translation, confidence scores

#### Audio Operations
- `POST /transcribe-audio` - Convert audio to text (Speech-to-Text)
  - Supports: MP3, WAV, M4A, AAC
  - Returns: Transcribed text, detected language
- `GET /audio/{audio_id}` - Retrieve generated audio file

#### Export
- `POST /export` - Generate PDF or TXT export
  - Parameters: content, language, format (pdf/txt)
  - Returns: Downloadable file

### Request/Response Examples

**Translate Text**
```bash
curl -X POST http://localhost:8000/translate-text \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "source_lang": "en", "target_lang": "gu"}'
```

**OCR + Translate Image**
```bash
curl -X POST http://localhost:8000/translate-image \
  -F "file=@image.jpg" \
  -F "target_lang=gu" \
  -F "ocr_engine=easyocr"
```

**Transcribe Audio**
```bash
curl -X POST http://localhost:8000/transcribe-audio \
  -F "file=@audio.mp3"
```

**Export PDF**
```bash
curl -X POST http://localhost:8000/export \
  -H "Content-Type: application/json" \
  -d '{"text": "Content here", "language": "gu", "format": "pdf"}' \
  --output result.pdf
```

---

## Usage

### Using the Web Interface

1. **Text Tab**: Paste or type text, select translation languages, and translate
2. **Image Tab**: Upload an image, select OCR engine and target language
3. **Audio Tab**: Record or upload audio for transcription
4. **Export**: Download results as PDF or TXT files

### Using the API Directly

The API is fully RESTful and can be integrated into any application:

```python
import requests

# Translate text
response = requests.post('http://localhost:8000/translate-text', json={
    'text': 'Hello',
    'source_lang': 'en',
    'target_lang': 'gu'
})
print(response.json())
```

---

## Configuration

### Supported Languages
- **English** (en)
- **Hindi** (hi)
- **Gujarati** (gu)

To add more languages:
1. Update OCR engine initialization in `advanced_ocr_api.py`
2. Add language codes to EasyOCR/PaddleOCR readers
3. Restart the application

### OCR Engines
All three engines are available by default:
- **EasyOCR**: Fast, accurate, supports 80+ languages
- **PaddleOCR**: Lightweight, good for detection and recognition
- **Tesseract**: Classic, reliable, requires system installation

Select engine via the frontend or `ocr_engine` parameter in API calls.

### Environment Variables
```bash
PYTHONUNBUFFERED=1
EASYOCR_MODULE_PATH=/path/to/models
```

---

## Requirements

### System Dependencies (Docker)
- Python 3.10
- FFmpeg (audio processing)
- Tesseract (OCR)
- OpenGL libraries
- Fonts (DejaVu, Indic)

### Python Packages
See `requirements_advanced_ocr.txt` for complete list. Key packages:
- fastapi >= 0.109.0
- easyocr >= 1.7.1
- paddleocr >= 2.7.3
- faster-whisper >= 1.1.0
- gTTS >= 2.5.1
- reportlab >= 4.0.9

---

## Project Structure

```
.
├── advanced_ocr_api.py           # Main FastAPI application
├── requirements_advanced_ocr.txt # Python dependencies
├── Dockerfile                     # Docker configuration
├── docker-compose.yml             # Docker Compose setup
├── README.md                      # This file
├── static/
│   └── index.html                 # Frontend SPA
└── temp/                          # Temporary files (audio, exports)
```

---

## Deployment

### Local Development
```bash
python advanced_ocr_api.py
```
Server runs on `http://localhost:8000`

### Docker Compose
```bash
docker compose up --build
```
Server runs on `http://localhost:8001` (as configured in docker-compose.yml)

### Custom Port/Host (Local)
```bash
uvicorn advanced_ocr_api:app --host 0.0.0.0 --port 8080
```

### Connecting Remote UI
If running API on a different host:
```
http://<api-host>:<api-port>/?api=http://<api-host>:<api-port>
```

---

## Troubleshooting

### Issue: OCR engine not initializing
- Ensure required Python packages are installed
- Check Docker build includes system dependencies
- Review logs for specific import errors

### Issue: Audio transcription fails
- Verify FFmpeg is installed: `ffmpeg -version`
- Check audio file format is supported (MP3, WAV, M4A)
- Increase timeout for large files

### Issue: Translation accuracy is low
- Verify source language detection
- Try a different OCR engine for images
- Check image quality for OCR tasks

### Issue: Docker build fails
- Clear Docker cache: `docker system prune`
- Rebuild with verbose output: `docker compose up --build --verbose`
- Check available disk space

### Port Already in Use
- Change port in `docker-compose.yml` for Docker
- Use `--port` flag for local Python execution

---

## Performance Tips

1. **Use EasyOCR** for accuracy, **PaddleOCR** for speed
2. **Compress images** before upload for faster processing
3. **GPU Support**: Install CUDA-compatible versions of PyTorch for acceleration
4. **Caching**: Remove old files from `temp/` directory periodically

---

## License

[Specify your license here - e.g., MIT, Apache 2.0, etc.]

## Contributing

Contributions welcome! Please submit issues and pull requests.

## Support

For issues, questions, or contributions, please open an issue in the repository.

