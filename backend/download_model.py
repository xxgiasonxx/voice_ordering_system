#!/usr/bin/env python3
"""Download Moonshine ASR model to the Docker image build cache."""
from huggingface_hub import snapshot_download

print("Downloading moonshine-ai/moonshine-streaming-tiny-zh model (~100MB)...")
snapshot_download("moonshine-ai/moonshine-streaming-tiny-zh")
print("Model download complete.")
