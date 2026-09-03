"""Malimg byte recovery (ADR-0002).

Nataraj's construction reshapes a file's byte vector to a width chosen by
file-size band and discards only the ``len mod width`` remainder. Flattening an
original-resolution Malimg image row-major therefore recovers the source file's
leading bytes exactly, losing under a kilobyte of tail.

That recovery is what gives the Malimg track an audio branch, `pefile` access
and FR7 at all, and with the instrument set deferred (ADR-0017) it is the
project's only source of parseable PE headers. It is the highest-consequence
gate in the project, which is why this module refuses rather than guesses.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

# Nataraj et al. (VizSec 2011), Table 1: image width by file size.
# Widths are powers of two and strictly increasing, which is what makes an
# observed width identifiable as a band rather than a resize artifact.
NATARAJ_WIDTH_BANDS: tuple[tuple[int, int, int], ...] = (
    #  min_bytes,   max_bytes,  width
    (0, 10 * 1024, 32),
    (10 * 1024, 30 * 1024, 64),
    (30 * 1024, 60 * 1024, 128),
    (60 * 1024, 100 * 1024, 256),
    (100 * 1024, 200 * 1024, 384),
    (200 * 1024, 500 * 1024, 512),
    (500 * 1024, 1000 * 1024, 768),
    (1000 * 1024, 1 << 62, 1024),
)

VALID_WIDTHS: frozenset[int] = frozenset(w for _, _, w in NATARAJ_WIDTH_BANDS)


class ResizedDistributionError(RuntimeError):
    """Raised when an image cannot have come from the original distribution.

    Silent recovery from a resized copy would produce plausible-looking garbage
    -- a byte stream with the right length and the wrong contents, which would
    train, evaluate and report without ever failing. Failing loudly here is the
    entire point of this module.
    """


def recover_bytes(image_path: str | Path, *, strict: bool = True) -> bytes:
    """Recover a Malimg sample's leading source bytes from its image.

    Args:
        image_path: an original-resolution Malimg PNG.
        strict: refuse widths outside the Nataraj band set. Turn this off only
            with a recorded reason -- a non-band width is the signature of a
            resized copy.

    Returns:
        The source file's leading bytes, short by ``len mod width`` (under 1KB).

    Raises:
        ResizedDistributionError: if the image is not plausibly original.
    """
    path = Path(image_path)
    with Image.open(path) as img:
        if img.mode != "L":
            raise ResizedDistributionError(
                f"{path.name}: mode {img.mode!r}, expected 'L'. A Malimg image is "
                "8-bit grayscale; anything else has been through a conversion "
                "that does not preserve byte values."
            )
        arr = np.asarray(img, dtype=np.uint8)

    if arr.ndim != 2:
        raise ResizedDistributionError(f"{path.name}: shape {arr.shape}, expected 2-D")

    height, width = arr.shape

    if strict and width not in VALID_WIDTHS:
        raise ResizedDistributionError(
            f"{path.name}: width {width} is not a Nataraj band width "
            f"{sorted(VALID_WIDTHS)}. This is a resized copy, and flattening it "
            "would produce plausible garbage rather than the source bytes."
        )
    if width == height and width in (32, 64, 128, 256):
        # A square image at a power-of-two side is the signature of the
        # circulated resized copies (the 64x64 malimg.npz especially). It can
        # legitimately occur, but only by coincidence, so it is worth a refusal
        # the caller must override deliberately.
        raise ResizedDistributionError(
            f"{path.name}: {width}x{height} square. This is the shape of the "
            "resized redistributions; if this sample is genuinely original, "
            "pass strict=False and record why in protocols/malimg_recovery.md."
        )

    return arr.reshape(-1).tobytes()


def looks_like_pe(data: bytes) -> bool:
    """Whether a recovered blob starts with a DOS header.

    Necessary, not sufficient: `pefile` parsing is the real check, and the
    Milestone 0 gate requires it. This is the cheap filter that runs first.
    """
    return data[:2] == b"MZ"


def width_for_size(n_bytes: int) -> int:
    """The width Nataraj's construction would have used for a file this size.

    Used to check a recovered length against the band it claims to come from.
    """
    for lo, hi, width in NATARAJ_WIDTH_BANDS:
        if lo <= n_bytes < hi:
            return width
    raise ValueError(f"no band covers {n_bytes} bytes")
