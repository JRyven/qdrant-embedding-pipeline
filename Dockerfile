# Dockerfile for Qdrant Tagging Pipeline
# Builds a minimal container for running the ML tagging pipeline

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for sentence-transformers and Qdrant
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Copy config (production config will be mounted or overridden)
COPY config/ ./config/

# Create data directory
RUN mkdir -p /data

# Set environment
ENV PYTHONPATH=/app

# Default command (can be overridden)
CMD ["python", "-m", "src.tagging.ingest", "--help"]
