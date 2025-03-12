FROM python:3.12-slim

# Add application sources with correct permissions for OpenShift  
USER 0
WORKDIR /app

# Copy requirements files
COPY requirements.txt Pipfile Pipfile.lock ./

# Install ALL system dependencies in one layer to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    libssl-dev \
    ninja-build \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir opencv-python-headless && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# For security, run as non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port for the Litestar application
EXPOSE 8000

# Start the Litestar application with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]