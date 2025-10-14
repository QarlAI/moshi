FROM nvcr.io/nvidia/cuda:12.8.0-cudnn-devel-ubuntu24.04 AS build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    curl \
    libbz2-dev \
    libffi-dev \
    libgdbm-dev \
    liblzma-dev \
    libncurses5-dev \
    libnss3-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    pkg-config \
    python3 \
    python3-dev \
    python3-pip \
    wget \
    zlib1g-dev \
    && \
    rm -rf /var/lib/apt/lists/*

## Install UV
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.12 

WORKDIR /workspace

ARG CUDA_COMPUTE_CAP=89

COPY moshi-server/uv.lock uv.lock
COPY moshi-server/pyproject.toml pyproject.toml
# RUN --mount=type=bind,source=moshi-server/uv.lock,target=uv.lock \
#     --mount=type=bind,source=moshi-server/pyproject.toml,target=pyproject.toml \
#     uv sync
RUN uv sync

COPY . .

# Build and install moshi-server from local source instead of crates.io
RUN LD_LIBRARY_PATH=$(python -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR"))') \
    CXXFLAGS="-include cstdint" \
    CUDA_COMPUTE_CAP=${CUDA_COMPUTE_CAP} \
    cargo install --path moshi-server --features cuda

COPY tts.toml .

# Default config path (can be overridden via TTS_CONFIG_PATH env var)
ENV TTS_CONFIG_PATH=./tts.toml

CMD ["sh", "-c", "uv run moshi-server worker --config ${TTS_CONFIG_PATH}"]