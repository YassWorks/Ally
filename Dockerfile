FROM python:3.13-alpine

# no pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# no buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apk add --no-cache \
    build-base \
    && rm -rf /var/cache/apk/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# this is purely for testing purposes
# no non-privileged user cuz i wanna check stuff out inside the container

COPY app/ ./app/
COPY main.py ./