FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir chromadb docling --extra-index-url https://download.pytorch.org/whl/cpu

COPY . .

RUN printf '#!/bin/sh\nexec python /app/main.py "$@"\n' > /usr/local/bin/ally \
    && chmod +x /usr/local/bin/ally

CMD ["/bin/bash"]
