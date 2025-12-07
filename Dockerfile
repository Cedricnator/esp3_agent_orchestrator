FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency definition
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy application code
COPY app ./app
COPY gunicorn_conf.py .

# Environment Defaults
ENV PYTHONUNBUFFERED=1

EXPOSE 33201

# Run with Gunicorn
CMD ["uv", "run", "gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
