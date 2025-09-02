FROM python:3.12-slim

LABEL maintainer="soheil.dalirii@gmail.com"

ENV PYTHONDONTWRITEBYTECODE=1  
ENV PYTHONUNBUFFERED=1          

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \          
    libpq-dev \                 
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
COPY .env .env  

RUN python manage.py collectstatic --noinput

RUN mkdir -p logs

EXPOSE 8000

CMD ["sh", "-c", "${DJANGO_CMD:-gunicorn config.wsgi:application --bind 0.0.0.0:8000}"]