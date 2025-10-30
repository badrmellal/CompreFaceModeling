# Hikvision Camera Integration with CompreFace

FROM python:3.9-slim

LABEL maintainer="MELLAL BADR"
LABEL description="Camera integration service for face recognition and access control"

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and video processing
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    gfortran \
    openexr \
    libopenblas-dev \
    python3-dev \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ /app/src/

# Copy wait-for-services script
COPY wait-for-services.sh /app/wait-for-services.sh
RUN chmod +x /app/wait-for-services.sh

# Create directories for logs and debug images
RUN mkdir -p /app/logs /app/logs/debug_images

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OPENCV_VIDEOIO_PRIORITY_FFMPEG=1

# Set working directory to where the Python script is located
WORKDIR /app/src

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1

# Run the camera service with wait script
CMD ["/app/wait-for-services.sh"]
