#!/usr/bin/env python3
"""Download Qwen3-ASR model to the Docker image build cache."""
from huggingface_hub import snapshot_download

print("Downloading Qwen/Qwen3-ASR-0.6B model (~2GB)...")
snapshot_download("Qwen/Qwen3-ASR-0.6B")
print("Model download complete.")