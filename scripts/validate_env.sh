#!/bin/bash

set -euo pipefail

ENV_FILE=".env"
REQUIRED_VARS=(
    "MODEL_FILENAME"
    "DEPLOYMENT_MODE"
)

OPTIONAL_VARS=(
    "CPU_THREADS"
    "GPU_LAYERS"
    "CONTEXT_SIZE"
    "MAX_TOKENS"
    "TEMPERATURE"
    "TOP_P"
    "API_KEY"
    "LOG_LEVEL"
    "LLAMA_PORT_CPU"
    "LLAMA_PORT_GPU"
    "API_PORT"
    "PROMETHEUS_PORT"
    "GRAFANA_PORT"
    "GRAFANA_PASSWORD"
)

echo "=== Environment Validation Script ==="

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "❌ Error: ${ENV_FILE} file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

echo "✅ Found ${ENV_FILE} file"

source "${ENV_FILE}"

echo "Validating required variables..."
for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        echo "❌ Error: Required variable ${var} is not set"
        exit 1
    else
        echo "✅ ${var}=${!var}"
    fi
done

echo "Checking optional variables..."
for var in "${OPTIONAL_VARS[@]}"; do
    if [[ -n "${!var:-}" ]]; then
        echo "✅ ${var}=${!var}"
    else
        echo "⚠️  ${var} not set (using default)"
    fi
done

echo "Validating deployment mode..."
if [[ "${DEPLOYMENT_MODE}" != "cpu" && "${DEPLOYMENT_MODE}" != "gpu" ]]; then
    echo "❌ Error: DEPLOYMENT_MODE must be 'cpu' or 'gpu', got '${DEPLOYMENT_MODE}'"
    exit 1
fi

echo "Checking if model file exists..."
if [[ ! -f "models/${MODEL_FILENAME}" ]]; then
    echo "❌ Error: Model file not found at models/${MODEL_FILENAME}"
    echo "Run: ./scripts/download_model.sh"
    exit 1
fi

echo "Validating Docker setup..."
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Error: Docker daemon is not running"
    exit 1
fi

if [[ "${DEPLOYMENT_MODE}" == "gpu" ]]; then
    echo "Validating NVIDIA Docker runtime..."
    if ! docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &> /dev/null; then
        echo "❌ Error: NVIDIA Docker runtime not properly configured"
        echo "Please install nvidia-docker2"
        exit 1
    fi
    echo "✅ NVIDIA Docker runtime verified"
fi

echo "✅ All validations passed"
echo "=== Environment Ready ==="