# Dockerfile

FROM python:3.9-slim

LABEL maintainer="soheil.dalirii@gmail.com"

WORKDIR /code

COPY requirements.txt /code/

RUN pip install -U pip && \
    pip install -r requirements.txt

COPY . /code/

EXPOSE 8000

# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
