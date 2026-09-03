"""Tests for src/preprocess/perturb.py (FR7 padding, ADR-0015)."""

from __future__ import annotations

import pytest

from src.preprocess.perturb import pad_bytes


def test_zero_strength_returns_unchanged():
    raw = b"\x01\x02\x03\x04" * 10
    assert pad_bytes(raw, 0.0, "zero") == raw
    assert pad_bytes(raw, 0.0, "random") == raw


def test_zero_composition_appends_zero_bytes():
    raw = b"\xff" * 100
    padded = pad_bytes(raw, 0.10, "zero")
    assert padded[:100] == raw
    assert padded[100:] == b"\x00" * 10
    assert len(padded) == 110


def test_random_composition_appends_correct_length():
    raw = b"\xff" * 100
    padded = pad_bytes(raw, 0.20, "random")
    assert padded[:100] == raw
    assert len(padded) == 120


def test_random_composition_deterministic_for_same_seed():
    raw = b"\xab" * 200
    p1 = pad_bytes(raw, 0.10, "random", seed=7)
    p2 = pad_bytes(raw, 0.10, "random", seed=7)
    assert p1 == p2


def test_random_composition_differs_across_seeds():
    raw = b"\xab" * 200
    p1 = pad_bytes(raw, 0.10, "random", seed=1)
    p2 = pad_bytes(raw, 0.10, "random", seed=2)
    assert p1 != p2


def test_random_padding_is_not_all_zero():
    raw = b"\x00" * 1000
    padded = pad_bytes(raw, 0.10, "random", seed=42)
    junk = padded[1000:]
    assert junk != bytes(len(junk))  # astronomically unlikely by chance


def test_empty_raw_stays_empty_regardless_of_strength():
    assert pad_bytes(b"", 0.20, "zero") == b""
    assert pad_bytes(b"", 0.20, "random") == b""


def test_rejects_unknown_composition():
    with pytest.raises(ValueError):
        pad_bytes(b"abc", 0.1, "purple")


def test_rejects_negative_strength():
    with pytest.raises(ValueError):
        pad_bytes(b"abc", -0.1, "zero")
