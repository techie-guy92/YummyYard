# Dockerfile

FROM python:3.12-slim

LABEL maintainer="soheil.dalirii@gmail.com"

WORKDIR /code

COPY requirements.txt /code/

RUN pip install -U pip && \
    pip install -r requirements.txt

COPY . /code/

EXPOSE 8000

# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["gunicorn", "config.wsgi:application", "--workers=4", "--bind=0.0.0.0:8000"]