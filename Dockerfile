FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

##### Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

##### Install system dependencies
##### nano is included to edit the config.json file easily if needed.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && apt-get install -y nano \
    && rm -rf /var/lib/apt/lists/*

##### Install Python dependencies
COPY requirements.txt .
RUN uv add -n -r requirements.txt

##### Copy project
COPY . .

##### Adding Ally to PATH
RUN printf '#!/bin/sh\nexec python /app/main.py "$@"\n' > /usr/local/bin/ally \
    && chmod +x /usr/local/bin/ally

CMD ["/bin/bash"]
