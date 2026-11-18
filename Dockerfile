FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/ally \
    PATH="/opt/ally/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends git nano \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra hf --no-install-project

COPY . .
RUN uv sync --frozen --no-dev --extra hf

CMD ["/bin/bash"]
