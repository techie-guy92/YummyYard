FROM python:3.12-slim

LABEL maintainer="soheil.dalirii@gmail.com"

ENV PYTHONDONTWRITEBYTECODE=1  
ENV PYTHONUNBUFFERED=1          

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    postgresql-client \
    procps \ 
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --uid 1000 --disabled-password --gecos '' webuser && \
    mkdir -p /app/logs /app/aws && \
    chown -R webuser:webuser /app && \
    chmod -R 755 /app/aws

USER webuser

EXPOSE 8000