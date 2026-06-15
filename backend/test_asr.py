"""
Tests for asr_stream.py - covers AudioBuffer, WAV header creation, order_diff_state.
Run: cd backend && python -m pytest test_asr.py -v
"""
import sys
import struct
import json
import pytest
from dataclasses import replace

# ---------------------------------------------------------------------------
# Import the module-under-test's pure functions & class.
# We patch setup/token/rag imports before the module is loaded so the test
# can run without Redis / ChromaDB / LLM infrastructure.
# ---------------------------------------------------------------------------
from unittest.mock import MagicMock, patch
import os
# No external ASR service needed – local transformers backend is used

_mock_rag = MagicMock()
_mock_setup = MagicMock()
_mock_setup.cus_choice = None
_mock_setup.vectorstore = None
_mock_setup.conn = None
_mock_setup.redis_client = MagicMock()
_mock_setup.redis_client.get.return_value = json.dumps([])
_mock_setup.redis_client.set = MagicMock()
_mock_token = MagicMock()
_mock_token.decrypt_token = MagicMock(return_value="mock_token")
_mock_token.verify_token = MagicMock(return_value="mock_token_id")

# Mock heavy external packages that aren't needed for unit tests
sys.modules["fastapi"] = MagicMock()
sys.modules["fastapi.responses"] = MagicMock()
sys.modules["httpx"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["dotenv"].load_dotenv = MagicMock()

# Mock qwen-asr and torch (not available / not needed in unit tests)
_qwen_asr_mock = MagicMock()
_qwen_asr_mock.Qwen3ASRModel = MagicMock()
sys.modules["qwen_asr"] = _qwen_asr_mock
sys.modules["torch"] = MagicMock()

sys.modules["setup"] = _mock_setup
sys.modules["rag"] = MagicMock()
sys.modules["rag.rag_morning_eat"] = _mock_rag
sys.modules["blueprint.token"] = _mock_token

from blueprint.asr_stream import (
    AudioBuffer,
    create_wav_header,
    raw_pcm_to_wav,
    order_diff_state,
    BYTES_PER_SECOND,
)


# ======================= AudioBuffer =======================
class TestAudioBuffer:
    def test_initial_state(self):
        buf = AudioBuffer(window_size=2.0, overlap=0.5)
        assert buf.last_final_text == ""
        assert buf.pending_text == ""
        assert len(buf.buffer) == 0
        assert buf.bytes_per_second == 32000
        assert buf.window_bytes == 64000   # 2.0 * 32000
        assert buf.overlap_bytes == 16000  # 0.5 * 32000

    def test_add_chunk_below_threshold_returns_none(self):
        buf = AudioBuffer(window_size=2.0, overlap=0.5)
        result = buf.add_chunk(b"\x00" * 100)
        assert result is None
        assert len(buf.buffer) == 100

    def test_add_chunk_exact_threshold_returns_full_window_and_retains_overlap(self):
        buf = AudioBuffer(window_size=2.0, overlap=0.5)
        chunk = b"\x01" * buf.window_bytes  # exactly 64000 bytes
        result = buf.add_chunk(chunk)
        assert result is not None
        assert len(result) == buf.window_bytes
        # overlap (last 0.5s = 16000 bytes) is retained for next window
        assert len(buf.buffer) == 16000

    def test_add_chunk_exceeds_threshold_triggers_window_and_keeps_overlap(self):
        buf = AudioBuffer(window_size=2.0, overlap=0.5)
        # first chunk: half window
        buf.add_chunk(b"A" * 32000)
        assert len(buf.buffer) == 32000
        # second chunk: pushes past threshold
        result = buf.add_chunk(b"B" * 34000)
        assert result is not None
        assert len(result) == 66000
        # overlap = 16000 bytes retained from end of the 66000-byte window
        # result was bytes of 32000 A + 34000 B = 66000 total
        # buffer should retain last 16000 bytes
        assert len(buf.buffer) == 16000

    def test_extract_new_part_empty_current(self):
        buf = AudioBuffer()
        assert buf.extract_new_part("") == ""

    def test_extract_new_part_current_starts_with_last_final(self):
        buf = AudioBuffer()
        buf.last_final_text = "我要一份"
        result = buf.extract_new_part("我要一份大杯美式")
        assert result == "大杯美式"

    def test_extract_new_part_last_final_inside_current(self):
        buf = AudioBuffer()
        buf.last_final_text = "大杯"
        result = buf.extract_new_part("給我一杯大杯拿鐵")
        assert result == "拿鐵"

    def test_extract_new_part_no_overlap_returns_full(self):
        buf = AudioBuffer()
        buf.last_final_text = "我要紅茶"
        result = buf.extract_new_part("再來一杯咖啡")
        assert result == "再來一杯咖啡"

    def test_extract_new_part_empty_last_final_returns_full(self):
        buf = AudioBuffer()
        buf.last_final_text = ""
        result = buf.extract_new_part("你好")
        assert result == "你好"

    def test_update_final_clears_pending(self):
        buf = AudioBuffer()
        buf.pending_text = "accumulated"
        buf.update_final("新文字")
        assert buf.last_final_text == "新文字"
        assert buf.pending_text == ""

    def test_flush_remaining_non_empty(self):
        buf = AudioBuffer()
        buf.buffer = bytearray(b"remaining data")
        result = buf.flush_remaining()
        assert result == b"remaining data"
        assert len(buf.buffer) == 0

    def test_flush_remaining_empty(self):
        buf = AudioBuffer()
        result = buf.flush_remaining()
        assert result is None


# ====================== WAV header =========================
class TestWavHeader:
    def test_create_wav_header_structure(self):
        data_len = 64000
        header = create_wav_header(data_len)
        # header should be exactly 44 bytes
        assert len(header) == 44
        # RIFF chunk descriptor
        assert header[0:4] == b"RIFF"
        # file size = data_len + 36
        assert struct.unpack_from("<I", header, 4)[0] == data_len + 36
        assert header[8:12] == b"WAVE"
        assert header[12:16] == b"fmt "
        # subchunk1 size = 16
        assert struct.unpack_from("<I", header, 16)[0] == 16
        # audio format = 1 (PCM)
        assert struct.unpack_from("<H", header, 20)[0] == 1
        # channels = 1
        assert struct.unpack_from("<H", header, 22)[0] == 1
        # sample rate = 16000
        assert struct.unpack_from("<I", header, 24)[0] == 16000
        # byte rate = 16000 * 2
        assert struct.unpack_from("<I", header, 28)[0] == 32000
        # block align = 2
        assert struct.unpack_from("<H", header, 32)[0] == 2
        # bits per sample = 16
        assert struct.unpack_from("<H", header, 34)[0] == 16
        # data chunk
        assert header[36:40] == b"data"
        assert struct.unpack_from("<I", header, 40)[0] == data_len

    def test_raw_pcm_to_wav_concatenation(self):
        pcm = b"\x00" * 100
        wav = raw_pcm_to_wav(pcm)
        assert len(wav) == 44 + 100
        assert wav[0:4] == b"RIFF"
        assert wav[44:] == pcm  # data section = raw PCM


# ===================== order_diff_state ===================
class TestOrderDiffState:
    def test_empty_states(self):
        old = {"items": []}
        new = {"items": []}
        diff = order_diff_state(old, new)
        assert diff == {"added": [], "removed": [], "modified": []}

    def test_item_added(self):
        old = {"items": []}
        new = {"items": [{"id": 1, "name": "美式", "quantity": 1}]}
        diff = order_diff_state(old, new)
        assert len(diff["added"]) == 1
        assert diff["added"][0]["id"] == 1
        assert diff["removed"] == []
        assert diff["modified"] == []

    def test_item_removed(self):
        old = {"items": [{"id": 1, "name": "美式", "quantity": 1}]}
        new = {"items": []}
        diff = order_diff_state(old, new)
        assert diff["added"] == []
        assert len(diff["removed"]) == 1
        assert diff["removed"][0]["id"] == 1
        assert diff["modified"] == []

    def test_quantity_modified(self):
        old = {"items": [{"id": 1, "name": "美式", "quantity": 1}]}
        new = {"items": [{"id": 1, "name": "美式", "quantity": 2}]}
        diff = order_diff_state(old, new)
        assert diff["added"] == []
        assert diff["removed"] == []
        assert len(diff["modified"]) == 1
        assert diff["modified"][0]["old"]["quantity"] == 1
        assert diff["modified"][0]["new"]["quantity"] == 2

    def test_customization_modified(self):
        old = {"items": [{"id": 1, "name": "美式", "quantity": 1, "customization": "無糖"}]}
        new = {"items": [{"id": 1, "name": "美式", "quantity": 1, "customization": "少糖"}]}
        diff = order_diff_state(old, new)
        assert len(diff["modified"]) == 1
        assert diff["modified"][0]["old"]["customization"] == "無糖"
        assert diff["modified"][0]["new"]["customization"] == "少糖"

    def test_no_change(self):
        old = {"items": [{"id": 1, "name": "美式", "quantity": 1}]}
        new = {"items": [{"id": 1, "name": "美式", "quantity": 1}]}
        diff = order_diff_state(old, new)
        assert diff == {"added": [], "removed": [], "modified": []}

    def test_mixed_changes(self):
        old = {"items": [
            {"id": 1, "name": "美式", "quantity": 1},
            {"id": 2, "name": "拿鐵", "quantity": 1},
            {"id": 3, "name": "紅茶", "quantity": 2},
        ]}
        new = {"items": [
            {"id": 1, "name": "美式", "quantity": 1},          # unchanged
            {"id": 2, "name": "拿鐵", "quantity": 2},           # quantity modified
            {"id": 4, "name": "奶茶", "quantity": 1},           # added (replaced #3)
        ]}
        diff = order_diff_state(old, new)
        assert len(diff["added"]) == 1
        assert diff["added"][0]["id"] == 4
        assert len(diff["removed"]) == 1
        assert diff["removed"][0]["id"] == 3
        assert len(diff["modified"]) == 1
        assert diff["modified"][0]["old"]["id"] == 2
        assert diff["modified"][0]["old"]["quantity"] == 1
        assert diff["modified"][0]["new"]["quantity"] == 2


# =================== Edge / Integration ====================
class TestIntegration:
    """End-to-end simulation of the sliding window pipeline (no network)."""

    def simulate_window_cycle(self, chunks: list[bytes]) -> list[str]:
        """Feed chunks into AudioBuffer and collect window outputs."""
        buf = AudioBuffer(window_size=2.0, overlap=0.5)
        windows = []
        for ch in chunks:
            win = buf.add_chunk(ch)
            if win is not None:
                windows.append(win.hex()[:20])  # just a fingerprint
        return windows

    def test_many_small_chunks_eventually_fire(self):
        # 4096-byte chunks (typical WebAudio ScriptProcessor size)
        chunks = [b"\x00" * 4096] * 20  # 81920 bytes total
        windows = self.simulate_window_cycle(chunks)
        assert len(windows) >= 1  # at least one window fired

    def test_single_large_chunk_fires_once(self):
        chunk = b"\x01" * (2 * BYTES_PER_SECOND)  # 2 seconds worth
        windows = self.simulate_window_cycle([chunk])
        assert len(windows) == 1