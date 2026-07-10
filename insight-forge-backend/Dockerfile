# Multi-stage production build for FastAPI backend
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements & configuration files
COPY pyproject.toml requirements.txt ./

# Install python dependencies including dev targets and python-multipart
RUN pip install --no-cache-dir -r requirements.txt .[dev] python-multipart

# Copy project files
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
