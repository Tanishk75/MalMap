"""Image branch preprocessing (Module Interface Spec Section 2; ADR-0007, ADR-0008).

Builds the M0 (channels=1) and M1 (channels=2) image tensor through one shared
pipeline, so a later Delta(M1 - M0) measures the entropy channel and not two
different preprocessing paths (ADR-0007). Every cached tensor is written
alongside an offset map (ADR-0008) recording enough of the reshape/resize
history to resolve a heatmap pixel back to a source byte range -- without it
FR6 attribution is unmeasurable.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from src.config import image_cache_path, image_offsets_path
from src.data.recover import ResizedDistributionError, recover_bytes, width_for_size

IMAGE_FILE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif")


def _parse_kaggle_bytes_file(path: Path) -> bytes:
    """BIG2015 `.bytes` format: '<address> <hex> <hex> ... <hex>' per line, the
    leading address label discarded. '??' marks a byte the competition scrubbed
    from the PE header (ADR-0003) and is treated as 0x00 -- there is no way to
    recover the true value on this track, and 0x00 is at least a fixed, stated
    convention rather than a guess dressed up as data."""
    out = bytearray()
    with open(path, "r", encoding="ascii", errors="replace") as f:
        for line in f:
            for tok in line.split()[1:]:
                out.append(0 if tok == "??" else int(tok, 16))
    return bytes(out)


def _load_raw_bytes(binary_path: str) -> bytes:
    """Dispatches on file extension: a Malimg image recovers via Nataraj
    flattening (ADR-0002, strict -- a resize failure must surface here, not be
    masked as "malformed input"); a BIG2015 `.bytes` file is a hex-dump text
    format; anything else (a benign PE, ADR-0018, or a raw instrument-set
    binary) is read directly."""
    path = Path(binary_path)
    suffix = path.suffix.lower()
    if suffix == ".bytes":
        return _parse_kaggle_bytes_file(path)
    if suffix in IMAGE_FILE_EXTENSIONS:
        return recover_bytes(path)
    return path.read_bytes()


def _shannon_entropy(window: np.ndarray) -> float:
    if window.size == 0:
        return 0.0
    counts = np.bincount(window, minlength=256)
    probs = counts[counts > 0] / window.size
    return float(-(probs * np.log2(probs)).sum())


def _entropy_channel(padded: np.ndarray, window: int) -> np.ndarray:
    """One Shannon-entropy value per non-overlapping `window`-byte block,
    repeated across that block's own positions so the result aligns
    pixel-for-pixel with the byte channel before either is resized.

    This is windowed, not sliding, entropy: `entropy_window` is explicitly
    OPEN until Milestone 1's sweep (src/config.py), and non-overlapping blocks
    are the cheaper of the two interpretations to compute at file scale. If
    the sweep prefers a true sliding window, this is the function to revisit."""
    n = padded.size
    values = np.empty(n, dtype=np.float32)
    for start in range(0, n, window):
        block = padded[start:start + window]
        values[start:start + len(block)] = _shannon_entropy(block)
    return values / 8.0  # max Shannon entropy for byte-valued data is 8 bits


def image_prep(
    sample_id: str,
    binary_path: str,
    channels: int = 2,
    target_shape: tuple[int, int] = (224, 224),
    entropy_window: int = 256,
) -> tuple[torch.Tensor, dict]:
    """Returns ([C, H, W] float32 tensor, offset map) and writes both to cache.

    channels=1 produces the M0 grayscale tensor, channels=2 adds the entropy
    channel. Caches to data_cache/image/{sample_id}.pt and
    data_cache/image/{sample_id}.offsets.json -- the offset map is not
    optional; a cached tensor without it is invalid (ADR-0008).

    Never raises on generic malformed input (missing file, truncated hex,
    empty binary) -- these degrade to an all-zero tensor of the requested
    shape. A `ResizedDistributionError` from the Malimg recovery gate is the
    one exception: that signal exists specifically to be loud (ADR-0002) and
    is never swallowed here.
    """
    if channels not in (1, 2):
        raise ValueError(f"channels must be 1 or 2, got {channels}")

    try:
        raw = _load_raw_bytes(binary_path)
    except ResizedDistributionError:
        raise
    except (OSError, ValueError):
        raw = b""

    n_original = len(raw)
    width = width_for_size(max(n_original, 1))
    height = max(1, -(-max(n_original, 1) // width))  # ceil division
    n_padded = height * width

    padded = np.frombuffer(raw.ljust(n_padded, b"\x00"), dtype=np.uint8)
    byte_matrix = padded.reshape(height, width)

    channel0 = torch.from_numpy(byte_matrix.astype(np.float32) / 255.0)
    channel0 = F.interpolate(
        channel0[None, None], size=target_shape, mode="bilinear", align_corners=False
    )[0, 0]

    if channels == 2:
        entropy_flat = _entropy_channel(padded, entropy_window)
        channel1 = torch.from_numpy(entropy_flat.reshape(height, width))
        channel1 = F.interpolate(
            channel1[None, None], size=target_shape, mode="bilinear", align_corners=False
        )[0, 0]
        tensor = torch.stack([channel0, channel1], dim=0)
    else:
        tensor = channel0[None]

    offset_map = {
        "sample_id": sample_id,
        "original_length": n_original,
        "reshape_width": width,
        "natural_height": height,
        "target_shape": list(target_shape),
        "entropy_window": entropy_window if channels == 2 else None,
    }

    cache_path = image_cache_path(sample_id)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(tensor, cache_path)

    offsets_path = image_offsets_path(sample_id)
    offsets_path.parent.mkdir(parents=True, exist_ok=True)
    with open(offsets_path, "w", encoding="utf-8") as f:
        json.dump(offset_map, f, indent=2)

    return tensor, offset_map
