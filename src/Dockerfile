FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including ca-certificates
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv pip install --system -r pyproject.toml

# Upgrade certifi for latest SSL certificates
RUN uv pip install --system --upgrade certifi urllib3

# Copy application code
COPY src/ ./src/
COPY templates/ ./templates/
COPY main.py .

# Create necessary directories
RUN mkdir -p data/raw data/processed logs output

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port (if needed for future web interface)
EXPOSE 8000

# Command to run the application
CMD ["python", "main.py"]