FROM python:3.12-slim

LABEL maintainer="soheil.dalirii@gmail.com"

ENV PYTHONDONTWRITEBYTECODE=1  
ENV PYTHONUNBUFFERED=1          

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Create non-root user and assign ownership
RUN adduser --disabled-password --gecos '' celeryuser && \
    mkdir -p /app/logs && \
    chown -R celeryuser /app

USER celeryuser

EXPOSE 8000