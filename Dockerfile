# Dockerfile for Hugging Face Spaces and other container hosts.
# HF Spaces convention: listen on 7860.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

# --timeout 0 = unlimited, so SSE streaming never gets killed by gunicorn.
CMD ["gunicorn", "-b", "0.0.0.0:7860", "-w", "1", "--timeout", "0", "app:app"]
