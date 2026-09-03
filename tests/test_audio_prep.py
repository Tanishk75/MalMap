"""Tests for src/preprocess/audio.py using synthetic raw bytes -- no real
Malimg/BIG2015 sample is needed to verify the cache contract itself."""

from __future__ import annotations

import pytest
import torch

import src.config as config
from src.data.recover import ResizedDistributionError
from src.preprocess.audio import audio_prep


@pytest.fixture(autouse=True)
def isolated_data_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_CACHE", tmp_path / "data_cache")


def _write_raw_binary(tmp_path, name, data):
    path = tmp_path / name
    path.write_bytes(data)
    return path


def test_audio_prep_shape_and_range(tmp_path):
    raw = bytes(range(256)) * 100  # 25600 bytes
    path = _write_raw_binary(tmp_path, "sample.exe", raw)

    tensor = audio_prep("a1", str(path), sample_rate=16000, n_mels=64, n_frames=32)

    assert tensor.shape == (1, 64, 32)
    assert tensor.dtype == torch.float32
    assert tensor.min() >= 0.0 and tensor.max() <= 1.0


def test_audio_prep_writes_cache(tmp_path):
    path = _write_raw_binary(tmp_path, "sample.exe", b"hello world" * 500)
    audio_prep("a2", str(path), n_mels=32, n_frames=16)

    cache_path = config.audio_cache_path("a2")
    assert cache_path.exists()
    loaded = torch.load(cache_path)
    assert loaded.shape == (1, 32, 16)


def test_audio_prep_idempotent(tmp_path):
    path = _write_raw_binary(tmp_path, "sample.exe", b"\x01\x02\x03\x04" * 1000)

    tensor1 = audio_prep("a3", str(path), n_mels=32, n_frames=16)
    tensor2 = audio_prep("a3", str(path), n_mels=32, n_frames=16)

    assert torch.equal(tensor1, tensor2)


def test_audio_prep_empty_file_does_not_raise(tmp_path):
    path = _write_raw_binary(tmp_path, "empty.exe", b"")
    tensor = audio_prep("a4", str(path), n_mels=16, n_frames=8)

    assert tensor.shape == (1, 16, 8)
    assert torch.all(tensor == 0)


def test_audio_prep_missing_file_does_not_raise(tmp_path):
    tensor = audio_prep("a5", str(tmp_path / "does_not_exist.exe"), n_mels=16, n_frames=8)
    assert tensor.shape == (1, 16, 8)


def test_audio_prep_short_file_does_not_raise(tmp_path):
    path = _write_raw_binary(tmp_path, "tiny.exe", b"\x42")
    tensor = audio_prep("a6", str(path), n_mels=16, n_frames=8)
    assert tensor.shape == (1, 16, 8)


def test_audio_prep_propagates_resized_distribution_error(tmp_path):
    from PIL import Image

    img_path = tmp_path / "resized.png"
    Image.new("L", (64, 64), color=1).save(img_path)

    with pytest.raises(ResizedDistributionError):
        audio_prep("a7", str(img_path))


def test_audio_prep_pads_short_spectrogram_to_n_frames(tmp_path):
    # A short-ish signal produces fewer than n_frames time steps; must be padded.
    path = _write_raw_binary(tmp_path, "sample.exe", b"\x10" * 4000)
    tensor = audio_prep("a8", str(path), n_mels=32, n_frames=64)
    assert tensor.shape == (1, 32, 64)


def test_audio_prep_truncates_long_spectrogram_to_n_frames(tmp_path):
    raw = bytes(range(256)) * 2000  # large file -> many time frames
    path = _write_raw_binary(tmp_path, "sample.exe", raw)
    tensor = audio_prep("a9", str(path), n_mels=32, n_frames=8)
    assert tensor.shape == (1, 32, 8)
