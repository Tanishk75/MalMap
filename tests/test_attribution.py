"""Tests for src/explain/attribution.py -- verifies the offset map that
image_prep writes actually carries what heatmap_to_byte_ranges needs."""

from __future__ import annotations

import numpy as np
import pytest

from src.explain.attribution import heatmap_to_byte_ranges


def _offset_map(**overrides):
    base = {
        "sample_id": "s1",
        "original_length": 32,
        "reshape_width": 8,
        "natural_height": 4,
        "target_shape": [4, 4],
        "entropy_window": 256,
    }
    base.update(overrides)
    return base


def test_identity_resize_maps_one_to_one():
    # target_shape == natural resolution: every pixel is exactly one byte.
    offset_map = _offset_map(reshape_width=4, natural_height=4, target_shape=[4, 4],
                              original_length=16)
    heatmap = np.arange(16, dtype=np.float32).reshape(4, 4)

    ranges = heatmap_to_byte_ranges(heatmap, offset_map)

    assert len(ranges) == 16
    starts = sorted(r[0] for r in ranges)
    assert starts == list(range(16))
    for start, end, score in ranges:
        assert end == start + 1


def test_downscaled_heatmap_ranges_stay_within_original_length():
    offset_map = _offset_map()
    heatmap = np.random.rand(4, 4).astype(np.float32)

    ranges = heatmap_to_byte_ranges(heatmap, offset_map)

    assert ranges  # non-empty
    for start, end, score in ranges:
        assert 0 <= start < end <= offset_map["original_length"]


def test_scores_match_input_heatmap():
    offset_map = _offset_map(reshape_width=4, natural_height=4, target_shape=[4, 4],
                              original_length=16)
    heatmap = np.zeros((4, 4), dtype=np.float32)
    heatmap[2, 3] = 0.75

    ranges = heatmap_to_byte_ranges(heatmap, offset_map)
    matching = [r for r in ranges if r[2] == pytest.approx(0.75)]
    assert len(matching) == 1
    start, end, score = matching[0]
    assert start == 2 * 4 + 3  # row 2, col 3 in a width-4 natural grid


def test_rejects_shape_mismatch():
    offset_map = _offset_map(target_shape=[4, 4])
    heatmap = np.zeros((8, 8), dtype=np.float32)
    with pytest.raises(ValueError):
        heatmap_to_byte_ranges(heatmap, offset_map)


def test_truncated_padding_never_exceeds_original_length():
    # natural grid (height*width) is larger than original_length -- the tail
    # is zero-padding image_prep added, not real file content.
    offset_map = _offset_map(reshape_width=8, natural_height=4, target_shape=[4, 4],
                              original_length=10)  # grid holds 32 bytes, file has 10
    heatmap = np.ones((4, 4), dtype=np.float32)

    ranges = heatmap_to_byte_ranges(heatmap, offset_map)
    assert all(end <= 10 for _, end, _ in ranges)
    assert max(end for _, end, _ in ranges) == 10
