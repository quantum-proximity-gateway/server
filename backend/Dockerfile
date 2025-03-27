FROM python:3.9-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    cmake \
    ninja-build \
    build-essential \
    libssl-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone --depth=1 --branch main https://github.com/open-quantum-safe/liboqs.git

WORKDIR /opt/liboqs
RUN mkdir build && cd build && \
    cmake -GNinja \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_INSTALL_PREFIX=/usr/local .. && \
    ninja && \
    ninja install


FROM python:3.9-slim

COPY --from=builder /usr/local /usr/local
ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH:-}"

# Set up a working directory
WORKDIR /app

# Install system dependencies required for dlib, OpenCV, and general builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    wget \
    curl \
    g++ \
    gcc \
    make \
    git \
    libssl-dev \
    ninja-build \
    libgtk2.0-dev \
    libboost-all-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    ffmpeg \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libxext-dev \
    libatlas-base-dev \
    libhdf5-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjxl-dev \
    pkg-config \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    gnupg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install a specific version of CMake (3.25.2)
RUN wget https://github.com/Kitware/CMake/releases/download/v3.25.2/cmake-3.25.2-linux-x86_64.sh -O /tmp/cmake.sh && \
    chmod +x /tmp/cmake.sh && \
    /tmp/cmake.sh --skip-license --prefix=/usr/local && \
    rm /tmp/cmake.sh && \
    cmake --version

# Install Pipenv
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pipenv

# Set environment variable to force Pipenv to use the same directory for the virtual environment
ENV PIPENV_VENV_IN_PROJECT=1

# Copy only Pipenv files first for better caching
COPY Pipfile Pipfile.lock ./

# Install dependencies inside the virtual environment
ARG BUILD_PKGS="wget build-essential cmake"
ARG CLANG_DEPS=""
ARG CLANG_PKGS="clang-15 lldb-15 lld-15"
RUN pipenv install --deploy --ignore-pipfile --python 3.9 && \
    pipenv run pip install --no-cache-dir "numpy<2" && \
    pipenv run pip install --no-cache-dir cmake==3.25.2

# Add LLVM repository key safely (fixes gnupg error)
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | gpg --dearmor | tee /usr/share/keyrings/llvm-snapshot-keyring.gpg > /dev/null

# Install LLVM toolchain
RUN echo "deb [signed-by=/usr/share/keyrings/llvm-snapshot-keyring.gpg] http://apt.llvm.org/bookworm/ llvm-toolchain-bookworm main" >> /etc/apt/sources.list && \
    echo "deb-src [signed-by=/usr/share/keyrings/llvm-snapshot-keyring.gpg] http://apt.llvm.org/bookworm/ llvm-toolchain-bookworm main" >> /etc/apt/sources.list && \
    echo "deb [signed-by=/usr/share/keyrings/llvm-snapshot-keyring.gpg] http://apt.llvm.org/bookworm/ llvm-toolchain-bookworm-15 main" >> /etc/apt/sources.list && \
    echo "deb-src [signed-by=/usr/share/keyrings/llvm-snapshot-keyring.gpg] http://apt.llvm.org/bookworm/ llvm-toolchain-bookworm-15 main" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y clang-15 lldb-15 lld-15

RUN pipenv run pip install --no-cache-dir opencv-python-headless imutils face-recognition setuptools litestar

# Copy the rest of the application
COPY . .

# Ensure correct user permissions
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose the required port
EXPOSE 8000

# Start the Litestar application with pipenv
CMD ["pipenv", "run", "python", "-m", "litestar", "run", "--host", "0.0.0.0", "--port", "8000"]
