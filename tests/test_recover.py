"""Round-trip tests for Malimg byte recovery (ADR-0002).

These do not need the Malimg dataset. They synthesise images the way Nataraj's
construction would have, then check that recovery returns the bytes that went
in -- which is the property the Milestone 0 gate depends on.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from data.recover import (  # noqa: E402
    ResizedDistributionError,
    looks_like_pe,
    recover_bytes,
    width_for_size,
)


def _write_nataraj_image(tmp_path: Path, payload: bytes, width: int) -> Path:
    """Build the image Nataraj's construction would produce for `payload`."""
    usable = len(payload) - (len(payload) % width)
    arr = np.frombuffer(payload[:usable], dtype=np.uint8).reshape(-1, width)
    path = tmp_path / "sample.png"
    Image.fromarray(arr, mode="L").save(path)
    return path


def test_round_trip_recovers_leading_bytes(tmp_path: Path) -> None:
    rng = np.random.default_rng(42)
    payload = b"MZ" + rng.integers(0, 256, 40_000, dtype=np.uint8).tobytes()
    width = width_for_size(len(payload))

    path = _write_nataraj_image(tmp_path, payload, width)
    recovered = recover_bytes(path)

    lost = len(payload) % width
    assert lost < 1024, "the discarded tail must stay under a kilobyte"
    assert len(recovered) == len(payload) - lost
    assert recovered == payload[: len(recovered)], "recovery must be exact, not approximate"


def test_pe_header_survives(tmp_path: Path) -> None:
    """The header is the part FR6 needs; it is at offset 0, so it always survives."""
    rng = np.random.default_rng(7)
    payload = b"MZ\x90\x00" + rng.integers(0, 256, 70_000, dtype=np.uint8).tobytes()
    path = _write_nataraj_image(tmp_path, payload, width_for_size(len(payload)))

    assert looks_like_pe(recover_bytes(path))


def test_refuses_a_resized_copy(tmp_path: Path) -> None:
    """A 64x64 square is the shape of the circulated resized redistributions."""
    arr = np.zeros((64, 64), dtype=np.uint8)
    path = tmp_path / "resized.png"
    Image.fromarray(arr, mode="L").save(path)

    with pytest.raises(ResizedDistributionError):
        recover_bytes(path)


def test_refuses_a_non_band_width(tmp_path: Path) -> None:
    arr = np.zeros((100, 300), dtype=np.uint8)
    path = tmp_path / "odd.png"
    Image.fromarray(arr, mode="L").save(path)

    with pytest.raises(ResizedDistributionError):
        recover_bytes(path)


@pytest.mark.parametrize(
    ("size", "expected"),
    [(5_000, 32), (20_000, 64), (50_000, 128), (80_000, 256), (300_000, 512)],
)
def test_width_bands(size: int, expected: int) -> None:
    assert width_for_size(size) == expected
