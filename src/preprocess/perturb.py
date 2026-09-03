"""FR7 padding perturbations (ADR-0015).

Applied to the raw byte stream BEFORE preprocessing -- a padded file has a
different length, so its image width band, offset map and spectrogram must
all be regenerated from scratch. Never served from a clean cache.
"""

from __future__ import annotations

import numpy as np

JUNK_COMPOSITIONS = ("zero", "random")


def pad_bytes(raw: bytes, strength: float, composition: str, seed: int = 0) -> bytes:
    """Appends junk bytes equal to `strength` fraction of len(raw).

    composition='zero' appends zero bytes; 'random' appends uniformly random
    bytes generated from `seed`. Perturbed preprocessing does not depend on
    model seed (ADR-0015) -- this `seed` is a padding-run seed, not one of
    the three training seeds, so the same (raw, strength, composition, seed)
    always regenerates byte-identically regardless of which model evaluates it.
    """
    if composition not in JUNK_COMPOSITIONS:
        raise ValueError(
            f"unknown junk_composition {composition!r}, expected one of {JUNK_COMPOSITIONS}"
        )
    if strength < 0:
        raise ValueError(f"strength must be >= 0, got {strength}")

    n_junk = round(len(raw) * strength)
    if composition == "zero":
        junk = bytes(n_junk)
    else:
        rng = np.random.RandomState(seed)
        junk = rng.randint(0, 256, size=n_junk, dtype=np.uint8).tobytes()

    return raw + junk
