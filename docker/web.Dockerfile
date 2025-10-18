# Lightweight Python base
FROM python:3.13-slim

# System deps (curl + netcat for healthchecks; build tools rarely needed because psycopg[binary])
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Env hygiene
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Install Python deps first (cache-friendly)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copy project (compose will mount in dev; this keeps image self-contained)
COPY . /app

# Expose Django dev port
EXPOSE 8000
