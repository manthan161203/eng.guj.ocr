FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    tesseract-ocr-guj \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    fonts-dejavu \
    fonts-indic \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_advanced_ocr.txt .
RUN pip install --no-cache-dir -r requirements_advanced_ocr.txt

COPY advanced_ocr_api.py .
COPY static/ ./static/

RUN mkdir -p /app/temp && chmod 777 /app/temp

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV EASYOCR_MODULE_PATH=/root/.EasyOCR

RUN mkdir -p /root/.EasyOCR/model

CMD ["uvicorn", "advanced_ocr_api:app", "--host", "0.0.0.0", "--port", "8000"]