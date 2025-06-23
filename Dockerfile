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
    mkdir build && cd build && \
    cmake .. -DLLAMA_CURL=ON -DLLAMA_SERVER=ON && \
    cmake --build . --config Release -j $(nproc)

FROM base as gpu-builder
RUN apt-get update && apt-get install -y \
    nvidia-cuda-toolkit \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/ggerganov/llama.cpp.git && \
    cd llama.cpp && \
    mkdir build && cd build && \
    cmake .. -DLLAMA_CUDA=ON -DLLAMA_CURL=ON -DLLAMA_SERVER=ON && \
    cmake --build . --config Release -j $(nproc)

FROM base as cpu-runtime
COPY --from=cpu-builder /app/llama.cpp/build/bin/llama-server /usr/local/bin/llama-server
COPY --from=cpu-builder /app/llama.cpp/build/bin/lib*.so* /usr/local/lib/
RUN mkdir -p /app/models /app/logs && ldconfig
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
EXPOSE 8080
CMD ["llama-server", "--host", "0.0.0.0", "--port", "8080"]

FROM base as gpu-runtime
RUN apt-get update && apt-get install -y \
    nvidia-cuda-toolkit \
    && rm -rf /var/lib/apt/lists/*
    
COPY --from=gpu-builder /app/llama.cpp/build/bin/llama-server /usr/local/bin/llama-server
COPY --from=gpu-builder /app/llama.cpp/build/bin/lib*.so* /usr/local/lib/
RUN mkdir -p /app/models /app/logs && ldconfig
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
EXPOSE 8080
CMD ["llama-server", "--host", "0.0.0.0", "--port", "8080"]