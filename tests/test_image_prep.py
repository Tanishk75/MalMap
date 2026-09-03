"""Tests for src/preprocess/image.py using synthetic raw bytes -- no real
Malimg/BIG2015 sample is needed to verify the cache contract itself."""

from __future__ import annotations

import json

import pytest
import torch

import src.config as config
from src.data.recover import ResizedDistributionError
from src.preprocess.image import _parse_kaggle_bytes_file, image_prep


@pytest.fixture(autouse=True)
def isolated_data_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_CACHE", tmp_path / "data_cache")


def _write_raw_binary(tmp_path, name, data):
    path = tmp_path / name
    path.write_bytes(data)
    return path


def test_image_prep_m1_two_channel_shape_and_range(tmp_path):
    raw = bytes(range(256)) * 20  # 5120 bytes, plain binary extension
    path = _write_raw_binary(tmp_path, "sample.exe", raw)

    tensor, offset_map = image_prep("s1", str(path), channels=2, target_shape=(64, 64))

    assert tensor.shape == (2, 64, 64)
    assert tensor.dtype == torch.float32
    assert tensor.min() >= 0.0 and tensor.max() <= 1.0
    assert offset_map["original_length"] == len(raw)
    assert offset_map["target_shape"] == [64, 64]
    assert offset_map["entropy_window"] == 256


def test_image_prep_m0_single_channel(tmp_path):
    raw = b"\x00\xff" * 100
    path = _write_raw_binary(tmp_path, "sample.exe", raw)

    tensor, offset_map = image_prep("s2", str(path), channels=1, target_shape=(32, 32))

    assert tensor.shape == (1, 32, 32)
    assert offset_map["entropy_window"] is None


def test_image_prep_rejects_bad_channels(tmp_path):
    path = _write_raw_binary(tmp_path, "sample.exe", b"abc")
    with pytest.raises(ValueError):
        image_prep("s3", str(path), channels=3)


def test_image_prep_writes_cache_files(tmp_path):
    path = _write_raw_binary(tmp_path, "sample.exe", b"hello world" * 50)
    image_prep("s4", str(path), channels=2, target_shape=(16, 16))

    assert config.image_cache_path("s4").exists()
    assert config.image_offsets_path("s4").exists()

    loaded_tensor = torch.load(config.image_cache_path("s4"))
    assert loaded_tensor.shape == (2, 16, 16)

    with open(config.image_offsets_path("s4"), encoding="utf-8") as f:
        loaded_map = json.load(f)
    assert loaded_map["sample_id"] == "s4"


def test_image_prep_idempotent(tmp_path):
    path = _write_raw_binary(tmp_path, "sample.exe", b"\x01\x02\x03\x04" * 30)

    tensor1, map1 = image_prep("s5", str(path), channels=2, target_shape=(16, 16))
    tensor2, map2 = image_prep("s5", str(path), channels=2, target_shape=(16, 16))

    assert torch.equal(tensor1, tensor2)
    assert map1 == map2


def test_image_prep_empty_file_does_not_raise(tmp_path):
    path = _write_raw_binary(tmp_path, "empty.exe", b"")
    tensor, offset_map = image_prep("s6", str(path), channels=2, target_shape=(8, 8))

    assert tensor.shape == (2, 8, 8)
    assert offset_map["original_length"] == 0


def test_image_prep_missing_file_does_not_raise(tmp_path):
    tensor, offset_map = image_prep(
        "s7", str(tmp_path / "does_not_exist.exe"), channels=1, target_shape=(8, 8)
    )
    assert tensor.shape == (1, 8, 8)
    assert offset_map["original_length"] == 0


def test_image_prep_propagates_resized_distribution_error(tmp_path):
    from PIL import Image

    # A square power-of-two grayscale PNG -- the signature recover_bytes refuses.
    img_path = tmp_path / "resized.png"
    Image.new("L", (64, 64), color=1).save(img_path)

    with pytest.raises(ResizedDistributionError):
        image_prep("s8", str(img_path), channels=2)


def test_parse_kaggle_bytes_file(tmp_path):
    text = "00401000 8B FF 55 ?? EC\n00401010 83 EC 44\n"
    path = tmp_path / "0.bytes"
    path.write_text(text)

    raw = _parse_kaggle_bytes_file(path)
    assert raw == bytes([0x8B, 0xFF, 0x55, 0x00, 0xEC, 0x83, 0xEC, 0x44])


def test_image_prep_reads_kaggle_bytes_file(tmp_path):
    text = "00401000 " + " ".join(["41"] * 300)
    path = tmp_path / "123.bytes"
    path.write_text(text)

    tensor, offset_map = image_prep("s9", str(path), channels=2, target_shape=(16, 16))
    assert tensor.shape == (2, 16, 16)
    assert offset_map["original_length"] == 300
