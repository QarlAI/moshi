FROM ghcr.io/astral-sh/uv:0.6.17-debian AS build

# Install Python 3.12 and other dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip curl cmake libssl-dev pkg-config python3-dev wget ca-certificates sudo portaudio19-dev

ARG UID=1000
ARG GID=1000
RUN groupadd -g ${GID} appgroup && \
    useradd -m -u ${UID} -g appgroup user && \
    usermod -aG sudo user && \
    echo "user ALL+=(ALL) NOPASSWD: ALL" >> /etc/sudoers

WORKDIR /workspace

COPY uv.lock . 
COPY pyproject.toml .
RUN uv run echo hello

ENTRYPOINT ["/bin/bash", "-c"]