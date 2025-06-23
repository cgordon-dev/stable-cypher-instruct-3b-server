#!/bin/bash

set -euo pipefail

MODEL_NAME="stable-cypher-instruct-3b.Q4_K_M.gguf"
MODEL_URL="https://huggingface.co/lakkeo/stable-cypher-instruct-3b/resolve/main/stable-cypher-instruct-3b.Q4_K_M.gguf"
MODEL_DIR="./models"
MODEL_PATH="${MODEL_DIR}/${MODEL_NAME}"

echo "=== Model Download Script ==="
echo "Model: ${MODEL_NAME}"
echo "Destination: ${MODEL_PATH}"

if [[ -f "${MODEL_PATH}" ]]; then
    echo "Model already exists at ${MODEL_PATH}"
    echo "Verifying integrity..."
    
    if [[ -f "${MODEL_PATH}.sha256" ]]; then
        echo "Checking SHA256 hash..."
        if sha256sum -c "${MODEL_PATH}.sha256" --quiet; then
            echo "✅ Model integrity verified"
            exit 0
        else
            echo "❌ Model integrity check failed, re-downloading..."
            rm -f "${MODEL_PATH}"
        fi
    else
        echo "⚠️  No checksum file found, proceeding with existing model"
        exit 0
    fi
fi

echo "Creating models directory..."
mkdir -p "${MODEL_DIR}"

echo "Downloading model from Hugging Face..."
echo "URL: ${MODEL_URL}"

if command -v wget &> /dev/null; then
    wget -O "${MODEL_PATH}" "${MODEL_URL}" --progress=bar:force:noscroll
elif command -v curl &> /dev/null; then
    curl -L -o "${MODEL_PATH}" "${MODEL_URL}" --progress-bar
else
    echo "❌ Error: Neither wget nor curl is available"
    exit 1
fi

echo "✅ Model downloaded successfully"

echo "Generating SHA256 checksum..."
sha256sum "${MODEL_PATH}" > "${MODEL_PATH}.sha256"

echo "Model information:"
ls -lh "${MODEL_PATH}"
echo "SHA256: $(sha256sum "${MODEL_PATH}" | cut -d' ' -f1)"

echo "=== Download Complete ==="