#!/usr/bin/env python3
"""
Pre-download Qwen3-ASR model to local cache.
This avoids DNS/network issues inside Docker containers.
Run this ONCE on your host (outside Docker) before `docker-compose up`::

    python scripts/download_asr_model.py

The model will be downloaded to `./hf_cache/` in the project root.
"""
import os
import sys

MODEL_NAME = os.getenv("QWEN_ASR_MODEL", "Qwen/Qwen3-ASR-0.6B")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pre-download Qwen3-ASR model for offline Docker use")
    parser.add_argument(
        "--skip-if-exists",
        action="store_true",
        help="Skip download if model already cached"
    )
    args = parser.parse_args()

    # Resolve project root (voice_ordering_system/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    cache_dir = os.path.join(project_root, "hf_cache")

    # Ensure cache dir exists
    os.makedirs(cache_dir, exist_ok=True)

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("[INFO] huggingface-hub not installed, installing now...")
        os.system(f"{sys.executable} -m pip install huggingface-hub")
        from huggingface_hub import snapshot_download

    # Check if already cached (--skip-if-exists)
    if args.skip_if_exists:
        try:
            local_path = snapshot_download(MODEL_NAME, cache_dir=cache_dir, local_files_only=True)
            print(f"[OK] Model already cached at: {local_path}")
            return
        except Exception:
            # Not cached, proceed to download
            pass

    print(f"[INFO] Downloading model: {MODEL_NAME}")
    print(f"[INFO] Cache directory: {cache_dir}")
    print("[INFO] This may take a few minutes (~2GB download)...")

    try:
        snapshot_download(
            MODEL_NAME,
            cache_dir=cache_dir,
            local_files_only=False,
        )
        print(f"[OK] Model successfully cached to: {cache_dir}")
        print("[TIP] You can now start Docker with: docker-compose up -d")
    except Exception as e:
        print(f"[ERROR] Failed to download model: {e}")
        print("[HINT] If you're in a region with slow HF access, try:")
        print("       export HF_ENDPOINT=https://hf-mirror.com")
        print("       python scripts/download_asr_model.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
