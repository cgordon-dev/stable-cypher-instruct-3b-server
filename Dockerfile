FROM ubuntu:22.04 as base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    python3 \
    python3-pip \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

FROM base as cpu-builder
RUN git clone https://github.com/ggerganov/llama.cpp.git && \
    cd llama.cpp && \
    make server LLAMA_CURL=1

FROM base as gpu-builder
RUN apt-get update && apt-get install -y \
    nvidia-cuda-toolkit \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/ggerganov/llama.cpp.git && \
    cd llama.cpp && \
    make server LLAMA_CUDA=1 LLAMA_CURL=1

FROM base as cpu-runtime
COPY --from=cpu-builder /app/llama.cpp/server /usr/local/bin/llama-server
RUN mkdir -p /app/models /app/logs
EXPOSE 8080
CMD ["llama-server", "--host", "0.0.0.0", "--port", "8080"]

FROM base as gpu-runtime
RUN apt-get update && apt-get install -y \
    nvidia-cuda-toolkit \
    && rm -rf /var/lib/apt/lists/*
    
COPY --from=gpu-builder /app/llama.cpp/server /usr/local/bin/llama-server
RUN mkdir -p /app/models /app/logs
EXPOSE 8080
CMD ["llama-server", "--host", "0.0.0.0", "--port", "8080"]