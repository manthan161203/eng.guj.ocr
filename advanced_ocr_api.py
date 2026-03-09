from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal, List
import io
import os
from PIL import Image
from googletrans import Translator
import numpy as np
from gtts import gTTS
import uuid
from langdetect import detect, DetectorFactory
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Optional Speech-to-Text (STT)
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Ensure consistent language detection
DetectorFactory.seed = 0

# Import OCR libraries
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

app = FastAPI(title="Advanced OCR and Translation API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OCR engines
ocr_engines = {}

# We'll initialize engines with support for multiple languages
# Note: EasyOCR/PaddleOCR might download models on first run for new languages
if EASYOCR_AVAILABLE:
    try:
        # Default with English, Hindi, and Gujarati support
        ocr_engines['easyocr'] = easyocr.Reader(['en', 'hi', 'gu'], gpu=False)
        print("✓ EasyOCR initialized with [en, hi, gu] support")
    except Exception as e:
        print(f"✗ EasyOCR initialization failed: {e}")

if PADDLEOCR_AVAILABLE:
    try:
        # PaddleOCR uses different lang codes or multiple instances for best results
        # For simplicity in this demo, we use 'en' as default, but it handles many chars
        ocr_engines['paddleocr'] = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        print("✓ PaddleOCR initialized")
    except Exception as e:
        print(f"✗ PaddleOCR initialization failed: {e}")

if TESSERACT_AVAILABLE:
    ocr_engines['tesseract'] = 'tesseract'
    print("✓ Tesseract available")

# Setup directories for static files and temp storage
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize translator
translator = Translator()

class TextInput(BaseModel):
    text: str

class TranscriptionResponse(BaseModel):
    text: str
    language: Optional[str] = None

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    target_lang_code: str
    ocr_engine: Optional[str] = None
    confidence: Optional[float] = None
    audio_url: Optional[str] = None

def extract_text_easyocr(image: Image.Image) -> tuple[str, float]:
    """Extract text using EasyOCR (most accurate for printed text)"""
    if 'easyocr' not in ocr_engines:
        raise Exception("EasyOCR not available")
    
    # Convert PIL image to numpy array
    img_array = np.array(image)
    
    # Perform OCR
    results = ocr_engines['easyocr'].readtext(img_array)
    
    # Extract text and calculate average confidence
    texts = []
    confidences = []
    
    for (bbox, text, conf) in results:
        texts.append(text)
        confidences.append(conf)
    
    extracted_text = ' '.join(texts)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    return extracted_text, avg_confidence

def extract_text_paddleocr(image: Image.Image) -> tuple[str, float]:
    """Extract text using PaddleOCR (very accurate, especially for complex layouts)"""
    if 'paddleocr' not in ocr_engines:
        raise Exception("PaddleOCR not available")
    
    # Convert PIL image to numpy array
    img_array = np.array(image)
    
    # Perform OCR
    results = ocr_engines['paddleocr'].ocr(img_array, cls=True)
    
    # Extract text and calculate average confidence
    texts = []
    confidences = []
    
    if results and results[0]:
        for line in results[0]:
            if line:
                text = line[1][0]
                conf = line[1][1]
                texts.append(text)
                confidences.append(conf)
    
    extracted_text = ' '.join(texts)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    return extracted_text, avg_confidence

def extract_text_tesseract(image: Image.Image) -> tuple[str, float]:
    """Extract text using Tesseract (baseline OCR)"""
    if 'tesseract' not in ocr_engines:
        raise Exception("Tesseract not available")
    
    # Perform OCR
    extracted_text = pytesseract.image_to_string(image, lang='eng')
    
    # Tesseract doesn't provide confidence in image_to_string
    # Use image_to_data for confidence
    try:
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        confidences = [int(conf) for conf in data['conf'] if conf != '-1']
        avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
    except:
        avg_confidence = 0.0
    
    return extracted_text, avg_confidence

def extract_text_from_image(
    image: Image.Image, 
    engine: str = 'auto'
) -> tuple[str, str, float]:
    """
    Extract text from image using specified OCR engine
    Returns: (extracted_text, engine_used, confidence)
    """
    if engine == 'auto':
        # Priority: EasyOCR > PaddleOCR > Tesseract
        if 'easyocr' in ocr_engines:
            engine = 'easyocr'
        elif 'paddleocr' in ocr_engines:
            engine = 'paddleocr'
        elif 'tesseract' in ocr_engines:
            engine = 'tesseract'
        else:
            raise Exception("No OCR engine available")
    
    # Use specified engine
    if engine == 'easyocr':
        text, conf = extract_text_easyocr(image)
    elif engine == 'paddleocr':
        text, conf = extract_text_paddleocr(image)
    elif engine == 'tesseract':
        text, conf = extract_text_tesseract(image)
    else:
        raise Exception(f"Unknown OCR engine: {engine}")
    
    return text, engine, conf

@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/api-info")
async def api_info():
    available_engines = list(ocr_engines.keys())
    return {
        "message": "Advanced OCR and Translation API",
        "available_ocr_engines": available_engines,
        "recommended_engine": "easyocr" if "easyocr" in available_engines else available_engines[0] if available_engines else "none",
        "endpoints": {
            "/translate-text": "POST - Translate text",
            "/translate-image": "POST - Extract text from image and translate",
            "/translate": "POST - Unified endpoint for both text and image",
            "/available-engines": "GET - List available OCR engines",
            "/audio/{audio_id}": "GET - Stream TTS audio",
            "/transcribe-audio": "POST - Transcribe audio to text (STT)",
            "/export": "POST - Export as PDF or TXT"
        }
    }

# Initialize Whisper model lazily (first request), so startup stays fast.
_whisper_model: Optional["WhisperModel"] = None

def _get_whisper_model() -> "WhisperModel":
    global _whisper_model
    if not WHISPER_AVAILABLE:
        raise HTTPException(status_code=501, detail="Speech-to-Text not available. Install 'faster-whisper' and rebuild.")
    if _whisper_model is None:
        # Model size can be changed via env; common options: tiny, base, small, medium, large-v3
        model_size = os.getenv("WHISPER_MODEL", "base")
        device = os.getenv("WHISPER_DEVICE", "cpu")
        compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        _whisper_model = WhisperModel(model_size, device=device, compute_type=compute_type)
    return _whisper_model

@app.get("/available-engines")
async def available_engines():
    """Get list of available OCR engines with descriptions"""
    engines_info = {}
    
    if 'easyocr' in ocr_engines:
        engines_info['easyocr'] = {
            "name": "EasyOCR",
            "description": "Deep learning-based OCR, highly accurate for printed text",
            "best_for": "Clear printed text, multiple fonts, mixed languages",
            "accuracy": "High"
        }
    
    if 'paddleocr' in ocr_engines:
        engines_info['paddleocr'] = {
            "name": "PaddleOCR",
            "description": "Baidu's OCR system, excellent for complex layouts",
            "best_for": "Complex layouts, documents, mixed text orientations",
            "accuracy": "Very High"
        }
    
    if 'tesseract' in ocr_engines:
        engines_info['tesseract'] = {
            "name": "Tesseract",
            "description": "Google's OCR engine, good baseline performance",
            "best_for": "Simple documents, standard fonts",
            "accuracy": "Medium"
        }
    
    return {
        "available_engines": engines_info,
        "recommendation": "Use 'auto' to automatically select the best available engine"
    }

@app.post("/translate-text", response_model=TranslationResponse)
async def translate_text(input_data: TextInput, target_lang: str = "gu"):
    """
    Translate text to specified target language
    """
    try:
        if not input_data.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Detect source language
        try:
            detected_lang = detect(input_data.text)
        except:
            detected_lang = 'en'
            
        # Translate
        translation = translator.translate(input_data.text, dest=target_lang)
        
        # Generate Audio URL (optional, can be called separately)
        audio_id = str(uuid.uuid4())
        audio_path = os.path.join(TEMP_DIR, f"{audio_id}.mp3")
        
        return TranslationResponse(
            original_text=input_data.text,
            translated_text=translation.text,
            source_language=detected_lang,
            target_language=translation.dest,
            target_lang_code=target_lang,
            audio_url=f"/audio/{audio_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")

@app.post("/translate-image", response_model=TranslationResponse)
async def translate_image(
    file: UploadFile = File(...),
    ocr_engine: Literal['auto', 'easyocr', 'paddleocr', 'tesseract'] = 'auto',
    target_lang: str = "gu"
):
    """
    Extract text from image using OCR and translate to specified language
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Extract text using specified OCR engine
        extracted_text, engine_used, confidence = extract_text_from_image(image, ocr_engine)
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No text found in image")
        
        # Detect source language
        try:
            detected_lang = detect(extracted_text)
        except:
            detected_lang = 'en'
            
        # Translate
        translation = translator.translate(extracted_text, dest=target_lang)
        
        audio_id = str(uuid.uuid4())
        
        return TranslationResponse(
            original_text=extracted_text.strip(),
            translated_text=translation.text,
            source_language=detected_lang,
            target_language=translation.dest,
            target_lang_code=target_lang,
            ocr_engine=engine_used,
            confidence=round(confidence, 2),
            audio_url=f"/audio/{audio_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/audio/{audio_id}")
async def get_audio(audio_id: str, text: str, lang: str = "gu"):
    """
    Generate and stream TTS audio
    """
    try:
        audio_path = os.path.join(TEMP_DIR, f"{audio_id}.mp3")
        
        if not os.path.exists(audio_path):
            tts = gTTS(text=text, lang=lang)
            tts.save(audio_path)
            
        return FileResponse(audio_path, media_type="audio/mpeg", filename=f"translation_{audio_id}.mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

@app.post("/transcribe-audio", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None)
):
    """
    Speech-to-Text (STT): Accepts an audio file and returns transcribed text.

    - file: audio upload (wav/mp3/m4a/webm/ogg...)
    - language: optional language code hint (e.g. 'en', 'gu', 'hi'). If omitted, auto-detect.
    """
    try:
        if not file.content_type or not file.content_type.startswith("audio/"):
            # Some browsers may send 'application/octet-stream' for recorded blobs
            # so we don't hard-fail on content-type; we only validate that something was uploaded.
            if not file.filename:
                raise HTTPException(status_code=400, detail="Audio file is required")

        audio_id = str(uuid.uuid4())
        src_path = os.path.join(TEMP_DIR, f"audio_{audio_id}_{file.filename or 'input'}")

        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty audio file")

        with open(src_path, "wb") as f:
            f.write(contents)

        model = _get_whisper_model()
        segments, info = model.transcribe(
            src_path,
            language=language,
            vad_filter=True
        )

        text_parts: List[str] = []
        for seg in segments:
            if seg.text:
                text_parts.append(seg.text.strip())

        text = " ".join([t for t in text_parts if t]).strip()
        if not text:
            raise HTTPException(status_code=400, detail="No speech detected in audio")

        return TranscriptionResponse(
            text=text,
            language=getattr(info, "language", None)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

def create_pdf(original: str, translated: str, src_lang: str, dest_lang: str, output_path: str):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "OCR & Translation Report")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 80, f"Source ({src_lang}):")
    c.setFont("Helvetica", 10)
    text_obj = c.beginText(50, height - 100)
    text_obj.textLines(original)
    c.drawText(text_obj)
    
    # Simple separator
    y_pos = text_obj.getY() - 20
    c.line(50, y_pos, width - 50, y_pos)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos - 20, f"Translation ({dest_lang}):")
    c.setFont("Helvetica", 10)
    # Note: ReportLab standard fonts don't support Gujarati/Hindi well without registration.
    # For now, we'll output as text. In a full implementation, we'd register a Unicode font.
    trans_obj = c.beginText(50, y_pos - 40)
    trans_obj.textLines(translated)
    c.drawText(trans_obj)
    
    c.save()

@app.post("/export")
async def export_document(
    original_text: str = Form(...),
    translated_text: str = Form(...),
    src_lang: str = Form(...),
    dest_lang: str = Form(...),
    format: Literal['pdf', 'txt'] = Form('pdf')
):
    """
    Export results as PDF or TXT
    """
    try:
        file_id = str(uuid.uuid4())
        if format == 'pdf':
            file_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
            create_pdf(original_text, translated_text, src_lang, dest_lang, file_path)
            return FileResponse(file_path, media_type="application/pdf", filename="translation.pdf")
        else:
            file_path = os.path.join(TEMP_DIR, f"{file_id}.txt")
            content = f"Source ({src_lang}):\n{original_text}\n\nTranslation ({dest_lang}):\n{translated_text}"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return FileResponse(file_path, media_type="text/plain", filename="translation.txt")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

@app.post("/translate", response_model=TranslationResponse)
async def translate_unified(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    ocr_engine: Literal['auto', 'easyocr', 'paddleocr', 'tesseract'] = Form('auto'),
    target_lang: str = Form('gu')
):
    """
    Unified endpoint: accepts either text or image file
    """
    try:
        extracted_text = ""
        engine_used = None
        confidence = None
        
        # If text is provided, use it
        if text and text.strip():
            extracted_text = text
        
        # If no text but file is provided, extract text from image
        elif file:
            if not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="File must be an image")
            
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            extracted_text, engine_used, confidence = extract_text_from_image(image, ocr_engine)
        
        else:
            raise HTTPException(status_code=400, detail="Either text or image file must be provided")
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No text found to translate")
        
        # Detect source language
        try:
            detected_lang = detect(extracted_text)
        except:
            detected_lang = 'en'
            
        # Translate
        translation = translator.translate(extracted_text, dest=target_lang)
        
        audio_id = str(uuid.uuid4())
        
        return TranslationResponse(
            original_text=extracted_text.strip(),
            translated_text=translation.text,
            source_language=detected_lang,
            target_language=translation.dest,
            target_lang_code=target_lang,
            ocr_engine=engine_used,
            confidence=round(confidence, 2) if confidence else None,
            audio_url=f"/audio/{audio_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("Advanced OCR and Translation API")
    print("="*60)
    print(f"Available OCR engines: {list(ocr_engines.keys())}")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)