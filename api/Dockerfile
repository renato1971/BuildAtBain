FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libjpeg62-turbo \
    libpng16-16 \
    librsvg2-2 \
    libharfbuzz0b \
    libfreetype6 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/output /app/logs /app/data /app/.cache && \
    chmod -R 777 /app/output /app/logs /app/data /app/.cache

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV HOME=/app
ENV UV_CACHE_DIR=/app/.cache/uv

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "api.api:app", "--host", "0.0.0.0", "--port", "8000"]