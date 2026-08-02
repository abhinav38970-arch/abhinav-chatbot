# Production-ready Dockerfile for FastAPI RAG Application
# Optimized for Render deployment

# Use official Python slim image for smaller size
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100

# Set working directory
WORKDIR /app

# Install system dependencies first (required for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Ensure backend directory exists and has proper permissions
RUN mkdir -p /app/backend/app/retrieval && \
    mkdir -p /app/backend/app/database && \
    chmod -R 755 /app/backend

# Create necessary directories for runtime files
RUN mkdir -p /app/backend/app/retrieval && \
    mkdir -p /app/backend/app/database && \
    mkdir -p /app/backend/app/logs

# Copy the pre-built FAISS index and metadata if they exist
COPY backend/app/retrieval/faiss.index /app/backend/app/retrieval/ || true
COPY backend/app/retrieval/meta.pkl /app/backend/app/retrieval/ || true
COPY backend/app/database/school_data.db /app/backend/app/database/ || true

# Set environment variables for production
ENV PORT=8000
ENV ENVIRONMENT=production

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]