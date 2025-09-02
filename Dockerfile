FROM python:3.12-slim

LABEL maintainer="soheil.dalirii@gmail.com"

ENV PYTHONDONTWRITEBYTECODE=1  
ENV PYTHONUNBUFFERED=1          

WORKDIR /app

RUN apt-get update && apt-get install -y curl \
    build-essential \          
    libpq-dev \                
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

RUN mkdir -p logs

EXPOSE 8000

ENTRYPOINT ["gunicorn", "config.wsgi:application"]
CMD ["--bind", "0.0.0.0:8000"]