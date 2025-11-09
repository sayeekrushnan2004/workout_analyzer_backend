FROM python:3.11-slim

# Install system dependencies required for OpenCV and MediaPipe
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgthread-2.0-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libgstreamer1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Force rebuild by copying timestamp (breaks Docker cache)
COPY .buildtime /tmp/.buildtime

# Expose port (Railway will override with PORT env var)
EXPOSE 8000

# Use sh -c to properly expand $PORT environment variable
CMD sh -c "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"
