FROM python:3.9-slim

WORKDIR /app

# System packages for yt-dlp and ffmpeg (required for MP3 extraction)
RUN apt-get update && \
    apt-get install -y gcc libpq-dev ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app/main.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app.main:app"]