# Build Stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies
COPY pyproject.toml .
RUN uv pip install --system -r pyproject.toml

# Run Stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy Application Code
COPY . .

# Environment
ENV PYTHONUNBUFFERED=1

# Expose Port
EXPOSE 8000

# Entrypoint
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
